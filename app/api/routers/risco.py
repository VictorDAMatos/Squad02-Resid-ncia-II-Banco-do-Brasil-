from fastapi import APIRouter

from app.services.fraude_service import conectar, processar_todas_transacoes

router = APIRouter(prefix="/classificacao", tags=["🎯 Classificação de Risco"])


@router.get("/risco")
def listar_risco_transacoes():
    with conectar() as conexao:
        resultados = processar_todas_transacoes(conexao)

    total_amarelas = sum(1 for item in resultados if item["risco"]["classificacao"] == "amarelo")
    total_vermelhas = sum(1 for item in resultados if item["risco"]["classificacao"] == "vermelho")

    return {
        "total_amarelas": total_amarelas,
        "total_vermelhas": total_vermelhas,
        "transacoes": [
            {
                "transacao_id": item["transacao_id"],
                "conta": item["conta"],
                "classificacao": item["risco"]["classificacao"],
                "nivel": item["risco"]["nivel"],
                "pontos": item["risco"]["pontos"],
                "motivo": item["risco"]["motivo"],
                "status_transacao": item["status_transacao"],
                "status_conta": item["status_conta"],
                "bloqueio_automatico": item["bloqueio_automatico"],
            }
            for item in resultados
        ],
    }
