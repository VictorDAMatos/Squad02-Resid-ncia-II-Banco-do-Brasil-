from pydantic import BaseModel

# Aqui será definido como os dados entram e saem da API (filtros)
class RespostaPadrao(BaseModel):
    mensagem: str
    sucesso: bool = True