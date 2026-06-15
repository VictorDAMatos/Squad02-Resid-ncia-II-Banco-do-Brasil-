from typing import Optional
from pydantic import BaseModel, Field


class TransacaoSchema(BaseModel):
    valor: float = Field(..., gt=0)
    data: str
    hora: str = "00:00"
    dia_semana: Optional[str] = None

    latitude: float = 0
    longitude: float = 0
    tentativas: int = 1

    tipo_transacao: str = "pix"
    dispositivo: str = "web"

    cidade: str = "Recife"
    estado: str = "PE"
    pais: str = "Brasil"

    categoria: str = "servicos"
