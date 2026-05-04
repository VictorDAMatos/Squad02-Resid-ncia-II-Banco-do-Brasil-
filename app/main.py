from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.api.routers import clientes, transacoes, inteligencia, analista, core_bancario, anomalies

# CONFIGURAÇÃO DE METADADOS
descricao_api = """
### API Banco do Brasil - Squad 02 🚀
Sistema modular de Core Bancário e Detecção de Fraudes com IA.
"""

app = FastAPI(
    title="API Banco do Brasil",
    description=descricao_api,
    version="2.0.0"
)

# CONEXÃO DOS ROUTERS
app.include_router(clientes.router)
app.include_router(transacoes.router)
app.include_router(inteligencia.router)
app.include_router(analista.router)
app.include_router(core_bancario.router)
app.include_router(transacoes.router)
app.include_router(anomalies.router)

# ROTA RAIZ
@app.get("/", tags=["Status"])
def root():
    return {
        "status": "Online",
        "versao": "2.0.0",
        "projeto": "Modular Architecture (Layered)"
    }

# SCALAR
@app.get("/scalar", include_in_schema=False)
def documentacao_scalar():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
      <head>
        <title>API Banco do Brasil - Scalar</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <script id="api-reference" data-url="/openapi.json"></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """)