from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import sqlite3

# TÍTULO E DESCRIÇÃO

descricao_api = """
### Bem-vindo à API do Banco do Brasil - Squad 02! 🚀

Esta API foi desenvolvida para:
* **Gerenciar Transações:** Criar, buscar e listar transações com filtros.
* **Detectar Anomalias:** Identificar movimentações suspeitas ou fora de hora.
* **Chatbot com IA:** Cadastrar clientes e simular interações com Inteligência Artificial.
"""

app = FastAPI(
    title="API Banco do Brasil",
    description=descricao_api,
    version="1.0.0",
    contact={
        "name": "Squad 02",
    }
)
# INICIALIZAÇÃO DOS BANCOS DE DADOS

def inicializar_banco_transacoes():
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta TEXT NOT NULL,
            cidade TEXT NOT NULL,
            tipo_transacao TEXT NOT NULL,
            dispositivo TEXT NOT NULL
        )
    ''')
    conexao.commit()
    conexao.close()

def inicializar_banco_ia():
    conexao = sqlite3.connect('banco_brasil_ai.sqlite')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cliente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Interacao_IA (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            mensagem_cliente TEXT NOT NULL,
            resposta_ia TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES Cliente(id)
        )
    ''')
    conexao.commit()
    conexao.close()

inicializar_banco_transacoes()
inicializar_banco_ia()



# MODELOS DE DADOS (Pydantic)

class Transacao(BaseModel):
    valor: float
    data: str
    hora: str
    categoria: str
    conta: str
    cidade: str
    tipo_transacao: str
    dispositivo: str

class DadosCliente(BaseModel):
    nome: str
    cpf: str

class DadosChat(BaseModel):
    cliente_id: int
    mensagem: str


# ROTA: TRANSAÇÕES E ANOMALIAS

@app.post("/transactions", status_code=201, tags=["💳 Transações Bancárias"], summary="Registrar nova transação")
def criar_transacao(t: Transacao):
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute('''
        INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (t.valor, t.data, t.hora, t.categoria, t.conta, t.cidade, t.tipo_transacao, t.dispositivo))
    conexao.commit()
    transacao_id = cursor.lastrowid
    conexao.close()
    return {"sucesso": True, "id_transacao": transacao_id, "mensagem": "Transação criada com sucesso!"}

@app.get("/transactions", tags=["💳 Transações Bancárias"], summary="Listar transações com filtros")
def listar_transacoes(
        categoria: Optional[str] = Query(None, description="Filtrar por categoria (ex: alimentacao)"),
        cidade: Optional[str] = Query(None, description="Filtrar por cidade (ex: Recife)"),
        valor_min: Optional[float] = Query(None, description="Valor mínimo da transação"),
        valor_max: Optional[float] = Query(None, description="Valor máximo da transação"),
        tipo_transacao: Optional[str] = Query(None, description="Filtrar por tipo (ex: pix, cartao)")
):
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    parametros = []

    if categoria:
        query += " AND categoria = ?"
        parametros.append(categoria)
    if cidade:
        query += " AND cidade = ?"
        parametros.append(cidade)
    if valor_min is not None:
        query += " AND valor >= ?"
        parametros.append(valor_min)
    if valor_max is not None:
        query += " AND valor <= ?"
        parametros.append(valor_max)
    if tipo_transacao:
        query += " AND tipo_transacao = ?"
        parametros.append(tipo_transacao)

    cursor.execute(query, parametros)
    resultados = cursor.fetchall()
    conexao.close()
    return {"total": len(resultados), "transacoes": [dict(row) for row in resultados]}

@app.get("/transactions/{id}", tags=["💳 Transações Bancárias"], summary="Buscar uma transação específica pelo ID")
def buscar_transacao_por_id(id: int):
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (id,))
    resultado = cursor.fetchone()
    conexao.close()
    if resultado is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return dict(resultado)

@app.get("/anomalies", tags=["🚨 Segurança e Anomalias"], summary="Detectar movimentações suspeitas")
def detectar_anomalias():
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    query_anomalias = '''
        SELECT * FROM transactions
        WHERE valor > 10000 OR hora BETWEEN '00:00' AND '05:00'
    '''
    cursor.execute(query_anomalias)
    resultados = cursor.fetchall()
    conexao.close()
    return {
        "anomalias_detectadas": len(resultados),
        "motivo": "Transações com valor atípico (>10k) ou horários suspeitos (madrugada)",
        "transacoes": [dict(row) for row in resultados]
    }


# ROTA : CLIENTES E CHAT IA

@app.post("/api/clientes", tags=["🤖 Atendimento IA"], summary="Cadastrar novo cliente")
def criar_cliente(cliente: DadosCliente):
    try:
        conexao = sqlite3.connect('banco_brasil_ai.sqlite')
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO Cliente (nome, cpf) VALUES (?, ?)", (cliente.nome, cliente.cpf))
        conexao.commit()
        return {"sucesso": True, "mensagem": "Cliente cadastrado com sucesso!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Erro: Este CPF já está cadastrado.")
    finally:
        conexao.close()


@app.post("/api/chat", tags=["🤖 Atendimento IA"], summary="Enviar mensagem para a Inteligência Artificial")
def conversar_com_ia(chat: DadosChat):
    try:
        conexao = sqlite3.connect('banco_brasil_ai.sqlite')
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM Cliente WHERE id = ?", (chat.cliente_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")

        resposta_simulada = f"Olá! Entendi que você disse: '{chat.mensagem}'. Como sou um assistente do BB, como posso ajudar?"

        cursor.execute(
            "INSERT INTO Interacao_IA (cliente_id, mensagem_cliente, resposta_ia) VALUES (?, ?, ?)",
            (chat.cliente_id, chat.mensagem, resposta_simulada)
        )
        conexao.commit()

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