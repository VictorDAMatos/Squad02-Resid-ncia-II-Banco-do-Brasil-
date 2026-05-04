from fastapi import APIRouter

router = APIRouter(prefix="/analista", tags=["Painel do Analista (US04)"])

@router.get("/contas-bloqueadas")
def listar_bloqueios():
    # Lista de contas suspensas por risco 3
    return {"bloqueadas": []}

@router.post("/desbloquear/{conta_id}")
def desbloquear_conta(conta_id: int):
    # Função para o analista reativar conta.
    return {"mensagem": f"Conta {conta_id} desbloqueada manualmente."}

# ROUTER (US04)