import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Inicializa a API
app = FastAPI(title="API Banco do Brasil - Squad 02")


# ==========================================
# 3.1 - ESTRUTURA DO BANCO DE DADOS (SQLite)
# ==========================================
def inicializar_banco():
    conexao = sqlite3.connect('banco_brasil_ai.sqlite')
    cursor = conexao.cursor()

    # Cria a primeira tabela
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Cliente
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       nome
                       TEXT
                       NOT
                       NULL,
                       cpf
                       TEXT
                       UNIQUE
                       NOT
                       NULL
                   )
                   ''')

    # Cria a segunda tabela logo em seguida (sem fechar o banco antes)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Interacao_IA
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       cliente_id
                       INTEGER
                       NOT
                       NULL,
                       mensagem_cliente
                       TEXT
                       NOT
                       NULL,
                       resposta_ia
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       cliente_id
                   ) REFERENCES Cliente
                   (
                       id
                   )
                       )
                   ''')
    conexao.commit()
    conexao.close()


inicializar_banco()


class DadosCliente(BaseModel):
    nome: str
    cpf: str


class DadosChat(BaseModel):
    cliente_id: int
    mensagem: str


# Endpoint 1: Criar Cliente
@app.post("/api/clientes")
def criar_cliente(cliente: DadosCliente):
    try:  # 3.4 - Tratamento de Exceções
        conexao = sqlite3.connect('banco_brasil_ai.sqlite')
        cursor = conexao.cursor()

        # Persistência
        cursor.execute("INSERT INTO Cliente (nome, cpf) VALUES (?, ?)", (cliente.nome, cliente.cpf))
        conexao.commit()

        return {"sucesso": True, "mensagem": "Cliente cadastrado com sucesso!"}

    except sqlite3.IntegrityError:
        # Caso de Falha: CPF já existe no banco (valores inválidos)
        raise HTTPException(status_code=400, detail="Erro: Este CPF já está cadastrado.")
    finally:
        conexao.close()


# Endpoint (2): Chat com IA (Simulação)
@app.post("/api/chat")
def conversar_com_ia(chat: DadosChat):
    # Entrada de dados: O 'chat' recebe o JSON do Frontend

    try:
        conexao = sqlite3.connect('banco_brasil_ai.sqlite')
        cursor = conexao.cursor()

        # Processamento: Verifica se o cliente existe
        cursor.execute("SELECT id FROM Cliente WHERE id = ?", (chat.cliente_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")

        # Integração com IA (Chama a API do ChatGPT/Gemini)

        resposta_simulada = f"Olá! Entendi que você disse: '{chat.mensagem}'. Como sou um assistente do BB, como posso ajudar?"

        # Salva no banco de dados
        cursor.execute(
            "INSERT INTO Interacao_IA (cliente_id, mensagem_cliente, resposta_ia) VALUES (?, ?, ?)",
            (chat.cliente_id, chat.mensagem, resposta_simulada)
        )
        conexao.commit()

        # Retorno para o Frontend
        return {
            "sucesso": True,
            "resposta_ia": resposta_simulada
        }

    except sqlite3.Error as e:

        raise HTTPException(status_code=500, detail=f"Erro interno no banco de dados: {e}")
    finally:
        conexao.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
