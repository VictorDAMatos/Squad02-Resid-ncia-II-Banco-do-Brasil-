from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from time import perf_counter

from app.api.routers import (
    clientes,
    transacoes,
    ia,
    analista,
    core_bancario,
    registros,
    risco,
    status,
    historico,
    antibot,
    monitoramento
)

from app.services.fraude_service import inicializar_tabelas_fraude
from app.services.registro_service import (
    inicializar_tabelas_registro,
    registrar_auditoria,
    registrar_log_operacao
)

descricao_api = """
### API Banco do Brasil - Squad 02 🚀
Sistema modular de Core Bancário, Detecção de Fraudes,
Auditoria e IA com Isolation Forest.
"""

app = FastAPI(
    title="API Banco do Brasil",
    description=descricao_api,
    version="2.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def preparar_banco_e_registros():
    inicializar_tabelas_registro()
    inicializar_tabelas_fraude()


@app.middleware("http")
async def middleware_logs_e_auditoria(request: Request, call_next):
    inicio = perf_counter()
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
            # Logs e auditoria não podem derrubar a operação principal.
            pass


# CONEXÃO DOS ROUTERS
app.include_router(clientes.router)
app.include_router(transacoes.router)
app.include_router(ia.router)
app.include_router(analista.router)
app.include_router(core_bancario.router)
app.include_router(registros.router)
app.include_router(risco.router)
app.include_router(status.router)
app.include_router(historico.router)
app.include_router(antibot.router)
app.include_router(monitoramento.router)


@app.get("/", tags=["Status"])
def root():
    return {
        "status": "Online",
        "versao": "2.1.0",
        "projeto": "Modular Architecture + IA Isolation Forest integrada"
    }


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

# Servir frontend pelo FastAPI: /static/analista/dashboard.html e /static/usuario/index.html
app.mount("/static", StaticFiles(directory="frontend"), name="static")
