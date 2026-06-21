"""Rotas da área do analista.

Router = camada de entrada HTTP.
Aqui ficam apenas endpoints, validação de parâmetros e chamada para o service.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import verificar_analista
from app.schemas.analista_schema import (
    CategoriasResponse,
    ContasBloqueadasResponse,
    DesbloqueioRequest,
    DetalheTransacaoResponse,
    FluxoConfirmacaoResponse,
    InjecaoSaldoRequest,
    MensagemResponse,
    NotificacaoRequest,
    NotificacoesResponse,
    ResolverAnaliseRequest,
    ResumoAnalistaResponse,
    SLAResponse,
    TimelineSuspeitoResponse,
    TransacoesFiltradasResponse,
)
from app.services.analista_service import AnalistaService


router = APIRouter(
    prefix="/analista",
    tags=["Painel do Analista (US04)"],
    dependencies=[Depends(verificar_analista)],
)
service = AnalistaService()


@router.get("/resumo", response_model=ResumoAnalistaResponse)
def resumo_movimentacoes():
    """Retorna KPIs e agrupamentos para o dashboard do analista."""
    return service.obter_resumo()


@router.post("/transacoes/{transacao_id}/processar-fluxo", response_model=FluxoConfirmacaoResponse)
def processar_fluxo_confirmacao(transacao_id: int):
    """4.1 + 4.3: percorre o fluxo de confirmação e aplica a ação automática pelo risco."""
    return service.processar_fluxo_confirmacao(transacao_id)


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


@router.get("/transacoes-por-risco", response_model=TransacoesFiltradasResponse)
def transacoes_por_risco(
    risco: Optional[str] = Query(None, description="baixo, medio ou alto."),
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros."),
):
    """4.4: filtra transações pela gravidade do risco."""
    return service.listar_transacoes_por_risco(risco=risco, limite=limite)


@router.get("/transacoes/{transacao_id}", response_model=DetalheTransacaoResponse)
def visualizar_transacao_manual(transacao_id: int):
    """4.5 + 4.11: detalhe manual da transação, risco e perfil de dispositivo."""
    return service.obter_detalhe_transacao(transacao_id)


@router.get("/contas-bloqueadas", response_model=ContasBloqueadasResponse)
def listar_bloqueios():
    """4.6: lista contas/transações marcadas como bloqueadas ou suspensas."""
    return service.listar_contas_bloqueadas()


@router.post("/desbloquear/{conta_id}", response_model=MensagemResponse)
def desbloquear_conta(conta_id: str, dados: DesbloqueioRequest):
    """4.6 + 4.10: desbloqueia conta exigindo justificativa e registrando auditoria."""
    return service.desbloquear_conta(
        conta_id=conta_id,
        justificativa=dados.justificativa,
        analista=dados.analista,
    )


@router.get("/suspeitos/{suspeito}/timeline", response_model=TimelineSuspeitoResponse)
def timeline_suspeito(
    suspeito: str,
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros."),
):
    """4.7: mostra resumo do suspeito, histórico, notificações, auditoria e dispositivos."""
    return service.montar_timeline_suspeito(suspeito=suspeito, limite=limite)


@router.post("/notificacoes", response_model=MensagemResponse)
def registrar_notificacao(dados: NotificacaoRequest):
    """4.8: registra uma mensagem de aviso enviada ao suspeito."""
    return service.registrar_notificacao(
        suspeito=dados.suspeito,
        mensagem=dados.mensagem,
        canal=dados.canal,
        transacao_id=dados.transacao_id,
        analista=dados.analista,
    )


@router.get("/notificacoes", response_model=NotificacoesResponse)
def listar_notificacoes(
    suspeito: Optional[str] = Query(None, description="CPF/conta do suspeito."),
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros."),
):
    """4.8: lista logs de notificações, opcionalmente filtrados por suspeito."""
    return service.listar_notificacoes(suspeito=suspeito, limite=limite)


@router.post("/injetar-saldo", response_model=MensagemResponse)
def injetar_saldo(dados: InjecaoSaldoRequest):
    """4.9: registra/injeta saldo de teste em uma conta. Rota protegida para analista."""
    return service.injetar_saldo(
        conta=dados.conta,
        valor=dados.valor,
        justificativa=dados.justificativa,
        analista=dados.analista,
    )


@router.get("/sla", response_model=SLAResponse)
def painel_sla(
    somente_abertas: bool = Query(False, description="Quando true, lista apenas análises em aberto."),
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros."),
):
    """4.12: painel de tempo de resposta das análises."""
    return service.listar_sla(somente_abertas=somente_abertas, limite=limite)


@router.post("/sla/{transacao_id}/resolver", response_model=MensagemResponse)
def resolver_analise(transacao_id: int, dados: ResolverAnaliseRequest):
    """4.12: conclui uma análise manual e calcula seu tempo total pelo SLA."""
    return service.resolver_analise(
        transacao_id=transacao_id,
        status_final=dados.status_final,
        justificativa=dados.justificativa,
        analista=dados.analista,
    )
