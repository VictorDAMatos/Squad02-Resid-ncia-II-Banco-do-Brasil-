from app.ai.inference.predictor import prever

def analisar_transacao_ia(transacao: dict):

    resultado = prever(transacao)

    return {
        "risco": resultado["risco"],
        "score": resultado["score"],
        "anomalia": resultado["anomalia"],
        "motivo": resultado["motivo"]
    }