"""Schemas da área do analista.

Os schemas funcionam como o "contrato" da API: eles documentam
quais campos entram e saem das rotas.
"""

from typing import Any
from pydantic import BaseModel, Field


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
