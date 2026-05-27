from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from time import perf_counter
from pathlib import Path
from app.api.routers import clientes, dashboard_ia, transacoes, ia, dashboard_ia, analista, core_bancario, anomalies, registros, risco, status, analise_manual
from app.services.registro_service import inicializar_tabelas_registro, registrar_auditoria, registrar_log_operacao

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

# CONFIGURAÇÃO DE METADADOS
descricao_api = """
### API Banco do Brasil - Squad 02 🚀
Sistema modular de Core Bancário e Detecção de Fraudes com IA.
"""

app = FastAPI(
    title="API Banco do Brasil",
    description=descricao_api,
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que qualquer página HTML acesse a API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _nome_acao(metodo: str) -> str:
    acoes = {
        "GET": "CONSULTAR",
        "POST": "CRIAR/EXECUTAR",
        "PUT": "ATUALIZAR",
        "PATCH": "ATUALIZAR",
        "DELETE": "EXCLUIR",
    }
    return acoes.get(metodo.upper(), "ACESSAR")


@app.on_event("startup")
def preparar_registros():
    inicializar_tabelas_registro()


@app.middleware("http")
async def middleware_logs_e_auditoria(request: Request, call_next):
    inicio = perf_counter()
    resposta = None
    status_code = 500

    try:
        resposta = await call_next(request)
        status_code = resposta.status_code
        return resposta
    finally:
        tempo_ms = round((perf_counter() - inicio) * 1000, 2)
        rota = request.url.path
        metodo = request.method.upper()
        query_params = str(request.query_params) if request.query_params else None
        ip_origem = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        try:
            registrar_log_operacao(
                metodo=metodo,
                rota=rota,
                query_params=query_params,
                status_code=status_code,
                tempo_ms=tempo_ms,
                ip_origem=ip_origem,
                user_agent=user_agent,
                detalhe="Registro automático gerado pelo middleware da API.",
            )

            rotas_ignoradas = {"/", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/scalar"}
            if rota not in rotas_ignoradas:
                ator_id = request.headers.get("x-analista-id") or "anonimo"
                ator_nome = request.headers.get("x-analista-nome") or "Analista não identificado"
                acao = _nome_acao(metodo)

                registrar_auditoria(
                    ator_id=ator_id,
                    ator_nome=ator_nome,
                    acao=acao,
                    recurso=rota,
                    metodo=metodo,
                    status_code=status_code,
                    ip_origem=ip_origem,
                    detalhe=f"{acao} {rota}",
                )
        except Exception:
            # O registro de log/auditoria não deve derrubar a operação principal da API.
            pass

# CONEXÃO DOS ROUTERS
app.include_router(clientes.router)
app.include_router(transacoes.router)
app.include_router(analista.router)
app.include_router(core_bancario.router)
app.include_router(anomalies.router)
app.include_router(registros.router)
app.include_router(risco.router)
app.include_router(status.router)
app.include_router(ia.router)
app.include_router(dashboard_ia.router)
app.include_router(analise_manual.router)

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# ROTA RAIZ
@app.get("/", tags=["Status"])
def root():
    return {
        "status": "Online",
        "versao": "2.1.0",
        "projeto": "Modular Architecture (Layered)",
        "docs": "/docs",
        "frontend_usuario": "/frontend/usuario/index.html",
        "frontend_analista": "/frontend/analista/index.html",
        "topicos_integrados": ["2.1 Classificação de risco", "2.3 Bloqueio automático", "2.6 Status de processamento", "4.1 a 4.12 Análise manual"]
    }


@app.get("/usuario", include_in_schema=False)
def abrir_front_usuario():
    return RedirectResponse(url="/frontend/usuario/index.html")


@app.get("/analista", include_in_schema=False)
def abrir_front_analista():
    return RedirectResponse(url="/frontend/analista/index.html")

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
