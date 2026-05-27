from typing import Optional

from fastapi import APIRouter, Query

from app.services.registro_service import listar_logs_operacoes, listar_registros_auditoria

router = APIRouter(prefix="/registros", tags=["📋 Logs e Auditoria (US03)"])


@router.get("/logs")
def consultar_logs(
    limite: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Quantidade máxima de registros retornados.",
    )
):
    """Retorna o histórico detalhado das operações feitas na API."""
    return {"total": limite, "logs": listar_logs_operacoes(limite=limite)}


@router.get("/auditoria")
def consultar_auditoria(
    limite: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Quantidade máxima de registros retornados.",
    ),
    ator_id: Optional[str] = Query(
        default=None,
        description="Filtra os registros por identificador do analista, quando informado.",
    ),
):
    """Retorna quem fez o quê, quando fez e em qual recurso do sistema."""
    return {
        "total": limite,
        "auditoria": listar_registros_auditoria(limite=limite, ator_id=ator_id),
    }
