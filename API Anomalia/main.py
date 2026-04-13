from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
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

    # CORE BANCÁRIO


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Agencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            numero TEXT NOT NULL,
            endereco TEXT
        )
    ''')

    # Como o Cliente já existe no banco de IA, aqui podemos ter um
    # Cliente_Core (ou manter só a Conta ligada direto à agência se preferir)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cliente_Core (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Conta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            saldo REAL DEFAULT 0,
            cliente_id INTEGER,
            agencia_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES Cliente_Core(id),
            FOREIGN KEY (agencia_id) REFERENCES Agencia(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            validade TEXT,
            cvv TEXT,
            conta_id INTEGER,
            FOREIGN KEY (conta_id) REFERENCES Conta(id)
        )
    ''')

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
    # Vai evitar que demore muito na hora de buscar as anomalisas (Por causa do gerador)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_valor ON transactions (valor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hora ON transactions (hora)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dispositivo ON transactions (dispositivo)')

    conexao.commit()
    conexao.close()


def inicializar_banco_ia():
    conexao = sqlite3.connect('banco_brasil_ai.sqlite')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cliente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefone TEXT NOT NULL,
            data_nascimento TEXT NOT NULL
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
from pydantic import BaseModel, Field


class AgenciaCreate(BaseModel):
    nome: str
    numero: str
    endereco: str


class ContaCreate(BaseModel):
    numero: str
    cliente_id: int
    agencia_id: int


class CartaoCreate(BaseModel):
    numero: str
    validade: str
    cvv: str
    conta_id: int


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
    nome: str = Field(..., min_length=3, description="Nome completo do cliente")
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF (com ou sem pontuação)")
    email: str = Field(..., description="E-mail válido do cliente")
    telefone: str = Field(..., description="Telefone com DDD")
    data_nascimento: str = Field(..., description="Data de nascimento (YYYY-MM-DD)")


class DadosChat(BaseModel):
    cliente_id: int
    mensagem: str

# ROTA: CORE BANCÁRIO

@app.post("/agencias", tags=["💲 Core Bancário"])
def criar_agencia(agencia: AgenciaCreate):
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO Agencia (nome, numero, endereco) VALUES (?, ?, ?)",
        (agencia.nome, agencia.numero, agencia.endereco)
    )
    conexao.commit()
    id_gerado = cursor.lastrowid
    conexao.close()
    return {"sucesso": True, "mensagem": "Agência criada!", "agencia_id": id_gerado}


@app.post("/cartoes", tags=["💲 Core Bancário"])
def criar_cartao(cartao: CartaoCreate):
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    # Verifica se a conta existe antes de criar o cartão
    cursor.execute("SELECT id FROM Conta WHERE id = ?", (cartao.conta_id,))
    if not cursor.fetchone():
        conexao.close()
        raise HTTPException(status_code=404, detail="Conta não encontrada!")

    cursor.execute(
        "INSERT INTO Cartao (numero, validade, cvv, conta_id) VALUES (?, ?, ?, ?)",
        (cartao.numero, cartao.validade, cartao.cvv, cartao.conta_id)
    )
    conexao.commit()
    conexao.close()
    return {"sucesso": True, "mensagem": "Cartão emitido e vinculado à conta!"}

# ROTA: TRANSAÇÕES E ANOMALIAS

@app.post("/transactions", status_code=201, tags=["💳 Transações Bancárias"], summary="Registrar nova transação")
def criar_transacao(t: Transacao):
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    # VALIDAÇÃO DO CORE BANCÁRIO

    # A conta da transação realmente existe no banco?
    cursor.execute("SELECT id FROM Conta WHERE numero = ?", (t.conta,))
    conta_db = cursor.fetchone()

    if not conta_db:
        conexao.close()
        raise HTTPException(
            status_code=404,
            detail=f"Transação negada: A conta de origem ({t.conta}) não existe no Core Bancário."
        )

    # Se for transação de cartão, o cartão existe e pertence a esta conta?
    if t.tipo_transacao in ['cartao_credito', 'cartao_debito']:
        numero_cartao_usado = t.dispositivo
        cursor.execute("SELECT id FROM Cartao WHERE numero = ? AND conta_id = ?", (numero_cartao_usado, conta_db[0]))
        if not cursor.fetchone():
            conexao.close()
            raise HTTPException(
                status_code=403,
                detail="Transação negada: Cartão inválido ou não pertence a esta conta."
            )

    # Se passou ileso pelas validações acima, registra a transação normalmente
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

    # "JOIN" liga a transação à conta e depois ao cliente
    query_anomalias = '''
        SELECT 
            t.id as id_transacao,
            t.valor,
            t.data,
            t.hora,
            t.categoria,
            t.tipo_transacao,
            t.dispositivo,
            t.cidade,
            c.nome as cliente_nome,
            c.cpf as cliente_cpf,
            co.numero as conta_numero,
            CASE
                WHEN t.valor > 10000 THEN 'Regra 1: Valor extremamente alto (> R$ 10.000)'
                WHEN t.hora BETWEEN '00:00' AND '05:00' THEN 'Regra 2: Transação em horário suspeito (Madrugada)'
                WHEN t.dispositivo = 'caixa_eletronico' AND t.valor > 5000 THEN 'Regra 3: Saque/Transferência de alto valor em Caixa Eletrônico'
                ELSE 'Anomalia detectada por múltiplos fatores'
            END as motivo_suspeita
        FROM transactions t
        LEFT JOIN Conta co ON t.conta = co.numero
        LEFT JOIN Cliente_Core c ON co.cliente_id = c.id
        WHERE t.valor > 10000
           OR t.hora BETWEEN '00:00' AND '05:00'
           OR (t.dispositivo = 'caixa_eletronico' AND t.valor > 5000)
    '''

    cursor.execute(query_anomalias)
    resultados = cursor.fetchall()
    conexao.close()

    return {
        "total_anomalias_detectadas": len(resultados),
        "regras_de_fraude_aplicadas": [
            "Regra 1: Valores acima de R$ 10.000,00",
            "Regra 2: Movimentações entre 00:00 e 05:00",
            "Regra 3: Uso de caixa eletrônico para valores > R$ 5.000,00"
        ],
        "transacoes_suspeitas": [dict(row) for row in resultados]
    }


# ROTA: CLIENTES E CHAT IA

@app.post("/api/clientes", tags=["🤖 Atendimento IA"])
def criar_cliente(cliente: DadosCliente):
    try:
        conexao = sqlite3.connect('banco_brasil_ai.sqlite')
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO Cliente (nome, cpf, email, telefone, data_nascimento)
            VALUES (?, ?, ?, ?, ?)
        ''', (cliente.nome, cliente.cpf, cliente.email, cliente.telefone, cliente.data_nascimento))
        conexao.commit()
        return {"sucesso": True, "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="CPF ou E-mail já cadastrado.")
    except Exception as e:
        # ISSO AQUI vai te mostrar no console o que realmente deu errado!
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")
    finally:
        conexao.close()


@app.post("/api/chat", tags=["🤖 Atendimento IA"], summary="Enviar mensagem para a Inteligência Artificial")
def conversar_com_ia(chat: DadosChat):
    try:
        conexao = sqlite3.connect('banco_brasil_ai.sqlite')
        cursor = conexao.cursor()

        # Busca o nome do cliente no banco de dados usando o ID
        cursor.execute("SELECT nome FROM Cliente WHERE id = ?", (chat.cliente_id,))
        resultado = cursor.fetchone()  # Traz a primeira linha encontrada

        if not resultado:
            raise HTTPException(status_code=404, detail="Cliente não encontrado no banco de dados.")

        nome_cliente = resultado[0]  # Extrai o nome da tupla retornada pelo banco

        # Resposta personalizada para o cliente
        resposta_simulada = f"Olá, {nome_cliente}! Entendi que você disse: '{chat.mensagem}'. Como sou o assistente virtual do Squad 02 em fase de testes, minha conexão com o cérebro real da IA será feita no futuro!"

        # Salva o histórico da conversa
        cursor.execute(
            "INSERT INTO Interacao_IA (cliente_id, mensagem_cliente, resposta_ia) VALUES (?, ?, ?)",
            (chat.cliente_id, chat.mensagem, resposta_simulada)
        )
        conexao.commit()

        return {
            "sucesso": True,
            "cliente": nome_cliente,
            "resposta_ia": resposta_simulada
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no banco de dados: {e}")
    finally:
        conexao.close()


# DOCUMENTAÇÃO SCALAR

@app.get("/scalar", include_in_schema=False)
def documentacao_scalar():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>API Banco do Brasil - Documentação</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          body { margin: 0; padding: 0; }
        </style>
      </head>
      <body>
        <script id="api-reference" data-url="/openapi.json"></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
