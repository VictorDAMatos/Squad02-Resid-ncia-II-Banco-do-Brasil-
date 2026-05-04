from fastapi import APIRouter
import sqlite3

# ROUTER (US05)
router = APIRouter(prefix="/anomalies", tags=["🤖 IA & Anomalias (US05)"])


@router.get("/")
def listar_anomalias():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute('''
                   SELECT *
                   FROM transactions
                   WHERE valor > 5000
                      OR hora BETWEEN '00:00' AND '05:59'
                   ''')

    anomalias = cursor.fetchall()
    conexao.close()

    return [dict(row) for row in anomalias]