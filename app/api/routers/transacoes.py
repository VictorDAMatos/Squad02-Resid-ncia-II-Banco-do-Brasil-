from fastapi import APIRouter, Query, HTTPException
import sqlite3
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/transacoes", tags=["Core Bancário (US01/US02)"])

class Transacao(BaseModel):
    valor: float
    data: str
    hora: str
    categoria: str
    conta: str
    cidade: str
    tipo_transacao: str
    dispositivo: str

@router.post("/")
def criar_transacao(transacao: Transacao):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    try:
        cursor.execute('''
            INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (transacao.valor, transacao.data, transacao.hora, transacao.categoria,
              transacao.conta, transacao.cidade, transacao.tipo_transacao, transacao.dispositivo))
        conexao.commit()
        return {"mensagem": "Transação realizada!", "id": cursor.lastrowid}
    finally:
        conexao.close()

@router.get("/")
def listar_transacoes(conta: Optional[str] = None):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    query = "SELECT * FROM transactions"
    params = []
    if conta:
        query += " WHERE conta = ?"
        params.append(conta)
    cursor.execute(query, params)
    return cursor.fetchall()