from fastapi import APIRouter

from app.services.fraude_service import conectar, processar_todas_transacoes

router = APIRouter(prefix="/status", tags=["✅ Status de Transação e Conta"])


@router.get("/Transacao")
def listar_status_transacoes():
    with conectar() as conexao:
        resultados = processar_todas_transacoes(conexao)

    return [
        {
            "transacao_id": item["transacao_id"],
            "conta": item["conta"],
            "classificacao_risco": item["risco"]["classificacao"],
            "nivel_risco": item["risco"]["nivel"],
            "transacao_status": item["status_transacao"],
        }
        for item in resultados
    ]


@router.get("/Conta")
def listar_status_conta():
    with conectar() as conexao:
        resultados = processar_todas_transacoes(conexao)

    contas = {}
    for item in resultados:
        conta = item["conta"]
        if conta not in contas:
            contas[conta] = {
                "conta": conta,
                "status": item["status_conta"],
                "total_vermelhos": 0,
                "total_amarelos": 0,
                "total_verdes": 0,
                "bloqueio_automatico": item["bloqueio_automatico"],
                "motivo_bloqueio": item["motivo_bloqueio"],
            }

        cor = item["risco"]["classificacao"]
        if cor == "vermelho":
            contas[conta]["total_vermelhos"] += 1
        elif cor == "amarelo":
            contas[conta]["total_amarelos"] += 1
        else:
            contas[conta]["total_verdes"] += 1

        if item["status_conta"] == "Bloqueada":
            contas[conta]["status"] = "Bloqueada"
        if item["bloqueio_automatico"]:
            contas[conta]["bloqueio_automatico"] = True
            contas[conta]["motivo_bloqueio"] = item["motivo_bloqueio"]

    return list(contas.values())
