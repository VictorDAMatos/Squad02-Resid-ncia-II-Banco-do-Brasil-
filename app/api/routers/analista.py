"""Rotas da área do analista.

Router = camada de entrada HTTP.
Aqui ficam apenas endpoints, validação de parâmetros e chamada para o service.
"""

from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.analista_schema import (
    CategoriasResponse,
    ContasBloqueadasResponse,
    MensagemResponse,
    ResumoAnalistaResponse,
    TransacoesFiltradasResponse,
)
from app.services.analista_service import AnalistaService


router = APIRouter(prefix="/analista", tags=["Painel do Analista (US04)"])
service = AnalistaService()


@router.get("/resumo", response_model=ResumoAnalistaResponse)
def resumo_movimentacoes():
    """Retorna KPIs e agrupamentos para o dashboard do analista."""
    return service.obter_resumo()


@router.get("/anomalias-detalhadas")
def anomalias_detalhadas(
    limite: int = Query(50, ge=1, le=500, description="Quantidade máxima de anomalias."),
):
    """Lista anomalias com a regra de risco que identificou cada transação."""
    return service.listar_anomalias_detalhadas(limite=limite)


@router.get("/categorias", response_model=CategoriasResponse)
def listar_categorias():
    """Retorna categorias disponíveis para preencher filtros no frontend."""
    return service.listar_categorias()


@router.get("/transacoes-filtradas", response_model=TransacoesFiltradasResponse)
def transacoes_filtradas(
    cpf: Optional[str] = Query(None, description="CPF do cliente."),
    conta: Optional[str] = Query(None, description="Conta bancária."),
    categoria: Optional[str] = Query(None, description="Categoria da transação."),
    valor_min: Optional[float] = Query(None, ge=0, description="Valor mínimo da transação."),
    valor_max: Optional[float] = Query(None, ge=0, description="Valor máximo da transação."),
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros."),
):
    """Filtra transações por CPF/conta, categoria e faixa de valor."""
    return service.filtrar_transacoes(
        cpf=cpf,
        conta=conta,
        categoria=categoria,
        valor_min=valor_min,
        valor_max=valor_max,
        limite=limite,
    )


@router.get("/contas-bloqueadas", response_model=ContasBloqueadasResponse)
def listar_bloqueios():
    """Lista contas/transações marcadas como bloqueadas ou suspensas."""
    return service.listar_contas_bloqueadas()


@router.post("/desbloquear/{conta_id}", response_model=MensagemResponse)
def desbloquear_conta(conta_id: int):
    """Desbloqueia uma conta pelo identificador informado."""
    return service.desbloquear_conta(conta_id)
