from fastapi import APIRouter, HTTPException
import sqlite3
from pydantic import BaseModel

router = APIRouter(prefix="/clientes", tags=["Clientes & Chatbot (US01)"])


class ChatIA(BaseModel):
    cliente_id: int
    mensagem: str


@router.post("/ia-chat")
def interagir_com_ia(chat: ChatIA):
    conexao = sqlite3.connect('data/banco_brasil_ai.sqlite')
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT nome FROM Cliente WHERE id = ?", (chat.cliente_id,))
        cliente = cursor.fetchone()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        resposta_simulada = f"Olá {cliente[0]}, eu sou o assistente do Squad 02!"

        cursor.execute(
            "INSERT INTO Interacao_IA (cliente_id, mensagem_cliente, resposta_ia) VALUES (?, ?, ?)",
            (chat.cliente_id, chat.mensagem, resposta_simulada)
        )
        conexao.commit()
        return {"sucesso": True, "resposta_ia": resposta_simulada}
    finally:
        conexao.close()