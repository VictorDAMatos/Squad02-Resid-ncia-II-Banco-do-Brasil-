from pydantic import BaseModel

class TransacaoSchema(BaseModel):

    valor: float
    data: str
    dia_semana: str

    latitude: float
    longitude: float

    tentativas: int

    tipo_transacao: str
    dispositivo: str

    cidade: str
    estado: str
    pais: str

    categoria: str