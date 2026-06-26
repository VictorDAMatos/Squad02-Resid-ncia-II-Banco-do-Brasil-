from fastapi import APIRouter
import sqlite3

router = APIRouter(prefix="/classificacao", tags=["🎯 Classificação de Risco"])

def classificar(t):
    valor = t['valor']
    hora = t['hora']
    dispositivo = t['dispositivo']

    # --- VERMELHA (Grave) ---
    if valor > 10000 or (hora >= '00:00' and hora <= '05:00'):
        return "vermelho", "Valor extremo ou madrugada profunda"
    
    # --- AMARELA (Leve) ---
    if valor > 5000 or (hora >= '23:00' or hora <= '06:00'):
        return "amarelo", "Valor alto ou horário suspeito"

    if dispositivo == "caixa_eletronico" and valor >= 5000:
        return "amarelo", "Valor elevado em caixa eletrónico"

    # --- VERDE (Normal) ---
    return "verde", "Transação dentro dos parâmetros normais"

@router.get("/risco")
def listar_risco_transacoes():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    # --- Criar coluna de risco ---
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN classificacao_risco TEXT")
    except sqlite3.OperationalError:
        pass 

    cursor.execute("SELECT id, conta, valor, data, hora, dispositivo FROM transactions")
    rows = cursor.fetchall()
    
    resultado_final = []
    total_amarelas = 0
    total_vermelhas = 0

    for row in rows:
        t = dict(row)
        
        cor, motivo = classificar(t)

        # --- Contadores ---
        if cor == "amarelo":
            total_amarelas += 1
        elif cor == "vermelho":
            total_vermelhas += 1

        cursor.execute('''
            UPDATE transactions 
            SET classificacao_risco = ? 
            WHERE id = ?
        ''', (cor, t['id']))

        # --- Transação ---
        resultado_final.append({
            "transacao_id": t['id'],
            "conta": t['conta'],
            "valor": t['valor'],
            "horario": t['hora'],
            "dispositivo": t['dispositivo'],
            "classificacao": cor,
            "motivo": motivo
        })

    conexao.commit()
    conexao.close()

    # --- Retorna resumo e transação ---
    return {
        "total_amarelas": total_amarelas,
        "total_vermelhas": total_vermelhas,
        "transacoes": resultado_final
    }