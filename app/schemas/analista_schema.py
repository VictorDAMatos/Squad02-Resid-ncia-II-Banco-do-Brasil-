"""Schemas da área do analista.

Os schemas funcionam como o "contrato" da API: eles documentam
quais campos entram e saem das rotas.
"""

from typing import Any
from pydantic import BaseModel, Field, validator


class KPIResumo(BaseModel):
    total: int = 0
    volume: float = 0
    media: float = 0
    maior: float = 0
    total_anomalias: int = 0


class AgrupamentoQuantidadeVolume(BaseModel):
    nome: str
    qtd: int = 0
    volume: float = 0


class AgrupamentoQuantidade(BaseModel):
    nome: str
    qtd: int = 0


class ResumoAnalistaResponse(BaseModel):
    kpis: KPIResumo
    por_categoria: list[AgrupamentoQuantidadeVolume]
    por_cidade: list[AgrupamentoQuantidadeVolume]
    por_dispositivo: list[AgrupamentoQuantidade]
    por_tipo: list[AgrupamentoQuantidadeVolume]
    por_hora: list[dict[str, Any]]
    ultimas_transacoes: list[dict[str, Any]]


class TransacoesFiltradasResponse(BaseModel):
    total: int
    limite: int
    transacoes: list[dict[str, Any]]
    avisos: list[str] = Field(default_factory=list)


class CategoriasResponse(BaseModel):
    categorias: list[str]


class MensagemResponse(BaseModel):
    mensagem: str


class ContasBloqueadasResponse(BaseModel):
    total: int
    bloqueadas: list[dict[str, Any]]
    avisos: list[str] = Field(default_factory=list)


class DesbloqueioRequest(BaseModel):
    justificativa: str = Field(
        ...,
        min_length=10,
        description="Motivo obrigatório para desbloquear a conta.",
        example="Cliente confirmou a compra via telefone.",
    )
    analista: str = Field("analista", description="Nome, matrícula ou e-mail do analista.")


class InjecaoSaldoRequest(BaseModel):
    conta: str = Field(..., min_length=1, description="Conta que receberá o saldo de teste.")
    valor: float = Field(..., gt=0, description="Valor a ser injetado para testes.")
    justificativa: str = Field(..., min_length=10, description="Motivo da injeção de saldo.")
    analista: str = Field("analista", description="Nome, matrícula ou e-mail do analista.")


class NotificacaoRequest(BaseModel):
    suspeito: str = Field(..., min_length=1, description="CPF, conta ou outro identificador do suspeito.")
    mensagem: str = Field(..., min_length=3, description="Mensagem enviada ao suspeito.")
    canal: str = Field("sistema", description="Canal usado: sistema, sms, email, whatsapp etc.")
    transacao_id: int | None = Field(None, description="Transação relacionada, se existir.")
    analista: str = Field("sistema", description="Responsável pelo envio/registro.")


class ResolverAnaliseRequest(BaseModel):
    status_final: str = Field(..., description="aprovada, bloqueada ou cancelada.")
    justificativa: str = Field(..., min_length=10, description="Justificativa da decisão.")
    analista: str = Field("analista", description="Nome, matrícula ou e-mail do analista.")

    @validator("status_final")
    def validar_status_final(cls, valor: str) -> str:
        permitido = {"aprovada", "bloqueada", "cancelada"}
        normalizado = valor.strip().lower()
        if normalizado not in permitido:
            raise ValueError("status_final deve ser: aprovada, bloqueada ou cancelada")
        return normalizado


class FluxoConfirmacaoResponse(BaseModel):
    transacao_id: int
    risco: str
    acao_automatica: str
    mensagem: str
    transacao: dict[str, Any]


class DetalheTransacaoResponse(BaseModel):
    transacao: dict[str, Any]
    risco: dict[str, Any]
    perfil_dispositivo: dict[str, Any]
    sla: dict[str, Any] | None = None


class TimelineSuspeitoResponse(BaseModel):
    suspeito: str
    perfil: dict[str, Any]
    transacoes: list[dict[str, Any]]
    notificacoes: list[dict[str, Any]]
    auditoria: list[dict[str, Any]]
    dispositivos: list[dict[str, Any]]


class SLAResponse(BaseModel):
    total: int
    analises: list[dict[str, Any]]


class NotificacoesResponse(BaseModel):
    total: int
    notificacoes: list[dict[str, Any]]
