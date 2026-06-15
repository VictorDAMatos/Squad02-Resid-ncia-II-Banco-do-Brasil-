from fastapi import APIRouter

router = APIRouter(prefix="/ia", tags=["🤖 Motor de IA (US05)"])

@router.post("/analisar-anomalia")
def analisar_com_isolation_forest(transacao_id: int):
    return {
        "status": "Em desenvolvimento",
        "info": "Aqui conectaremos o modelo .pkl da Floresta de Isolamento"
    }

@router.get("/relatorio-fraudes")
def gerar_relatorio_ia():

   # Relatório automático para o analista.

    return {"relatorio": "Gráficos de anomalias detectadas pela IA"}

# Router (US05)