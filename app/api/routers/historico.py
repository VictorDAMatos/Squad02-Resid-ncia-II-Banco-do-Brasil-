from fastapi import APIRouter
import sqlite3

router = APIRouter(prefix="/historico", tags=["📜 Histórico de Transações"])

@router.get("/transacoes")
def listar_historico_transacoes():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    # Faz apenas a leitura dos dados existentes
    cursor.execute("""
        SELECT id, conta, valor, data, hora, dispositivo 
        FROM transactions
    """)
    rows = cursor.fetchall()

    resultado_historico = []

    # Organiza apenas as informações
    for row in rows:
        t = dict(row)
        
        resultado_historico.append({
            "transacao_id": t["id"],
            "conta": t["conta"],
            "dados_transacao": {
                "valor": t["valor"],
                "data": t["data"],
                "hora": t["hora"],
                "dispositivo": t["dispositivo"]
            }
        })

    conexao.close()

    return resultado_historico