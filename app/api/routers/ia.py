from fastapi import APIRouter

from app.ai.inference.predictor import prever
from app.schemas.ia_schema import TransacaoSchema

router = APIRouter(
    prefix="/ia",
    tags=["IA"]
)

@router.post("/analisar")
def analisar_transacao(transacao: TransacaoSchema):

    resultado = prever(transacao.dict())

    return resultado