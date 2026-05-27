from fastapi import APIRouter

from app.services.fraude_service import conectar

router = APIRouter(
    prefix="/ia",
    tags=["Dashboard IA"]
)

@router.get("/dashboard")
def dashboard_ia():

    with conectar() as conexao:

        total = conexao.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        suspeitas = conexao.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE status_transacao = 'EM_ANALISE'
            """
        ).fetchone()[0]

        bloqueadas = conexao.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE status_transacao = 'BLOQUEADA'
            """
        ).fetchone()[0]

    return {
        "total_transacoes": total,
        "suspeitas": suspeitas,
        "bloqueadas": bloqueadas,
        "taxa_fraude": round(
            (bloqueadas / total) * 100 if total else 0,
            2
        )
    }