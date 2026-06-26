from fastapi import APIRouter
import sqlite3
from app.api.routers.risco import classificar

router = APIRouter(prefix="/status", tags=["✅ Status de Transação e Conta"])

def classificar_status_transacao(t):
    cor = t['classificacao_risco']

    # --- PENDENTE ---
    if cor == 'vermelho':
        return 'pendente'
    
    # --- EM ANALISE ---
    if cor == 'amarelo':
        return 'em análise'
    
    # --- APROVADA ---
    return 'aprovada'

@router.get("/Transacao")
def listar_status_transacoes():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    
    tabela = "transactions"
    coluna_obrigatoria = "classificacao_risco"

    cursor.execute(f"PRAGMA table_info({tabela});")
    colunas = [linha[1] for linha in cursor.fetchall()]

    if coluna_obrigatoria in colunas:
    # --- Criar coluna de status de transaçao ---
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN status_transacao TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute("SELECT id, conta, classificacao_risco FROM transactions")
        rows = cursor.fetchall()

        resultado_transacao = []

        for row in rows:
            t = dict(row)

            statusTransacao = classificar_status_transacao(t)

            cursor.execute('''
                UPDATE transactions 
                SET status_transacao = ? 
                WHERE id = ?
            ''', (statusTransacao, t['id']))


        # --- Transação ---
            resultado_transacao.append({
                'transacao_id': t['id'],
                'conta': t['conta'],
                'transacao_status': statusTransacao
            })

        conexao.commit()
        conexao.close()

        return resultado_transacao
    else:
        return f"Erro: A coluna '{coluna_obrigatoria}' não foi encontrada na tabela '{tabela}'."

@router.get("/Conta")
def listar_status_conta():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    tabela = "transactions"
    coluna_obrigatoria = "classificacao_risco"

    cursor.execute(f"PRAGMA table_info({tabela});")
    colunas = [linha[1] for linha in cursor.fetchall()]

    if coluna_obrigatoria in colunas:

    # --- Criar coluna de status de conta ---
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN status_conta TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute("SELECT conta, classificacao_risco FROM transactions")
        rows = cursor.fetchall()
    
        contagem_contas = {}

        for row in rows:
            t = dict(row)
            n_conta = t['conta']
            cor = t['classificacao_risco']

        # --- Adiciona a contagem_contas ---
            if n_conta not in contagem_contas:
                contagem_contas[n_conta] = {"amarelo": 0, "vermelho": 0, "verde": 0}

        # --- Soma +1 na cor ---
            if cor in contagem_contas[n_conta]:
                contagem_contas[n_conta][cor] += 1

        resultado_final = []
        for conta in contagem_contas:
            cores = contagem_contas[conta]
        
        # --- Coloca statua da conta: ativa ou bloqueada ---
            if cores["vermelho"] > 0 or cores["amarelo"] > 2:
                status_final = "Bloqueada"
            else:
                status_final = "Ativa"
        
            cursor.execute('''
                UPDATE transactions 
                SET status_conta = ? 
                WHERE conta = ?
            ''', (status_final, conta))

        # --- Retorna conta, status e qnt de cores ---
            resultado_final.append({
                "conta": conta,
                "status": status_final,
                "total_vermelhos": cores["vermelho"],
                "total_amarelos": cores["amarelo"],
                "total_verdes": cores["verde"]
            })

        conexao.commit()
        conexao.close()

        return resultado_final
    else:
        return f"Erro: A coluna '{coluna_obrigatoria}' não foi encontrada na tabela '{tabela}'."
