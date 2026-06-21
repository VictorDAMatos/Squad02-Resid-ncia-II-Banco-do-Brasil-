from fastapi import APIRouter, HTTPException, Query

from app.core.security import contem_padrao_suspeito, mascarar_dados_sensiveis

router = APIRouter(prefix="/seguranca", tags=["🔒 Segurança"])


@router.get("/status")
def status_seguranca():
    """Mostra as camadas de seguranca aplicadas na API."""
    return {
        "status": "ativo",
        "requisito": "6.3 Segurança",
        "camadas": [
            "Validação global de parâmetros contra padrões comuns de SQL Injection.",
            "Uso de consultas parametrizadas nos endpoints que acessam SQLite.",
            "Headers HTTP de segurança aplicados nas respostas da API.",
            "Helpers para mascaramento de dados sensíveis, como CPF, e-mail, cartão, CVV e tokens.",
            "Bloqueio de requisições com comandos SQL perigosos antes do acesso aos routers.",
        ],
        "endpoints_protegidos": "Todos os endpoints registrados na aplicação FastAPI.",
    }


@router.get("/validar-entrada")
def validar_entrada(valor: str = Query(..., min_length=1, max_length=200)):
    """Endpoint simples para testar a camada de validação de entradas."""
    if contem_padrao_suspeito(valor):
        raise HTTPException(
            status_code=400,
            detail="Entrada bloqueada por conter padrão suspeito.",
        )

    return {
        "seguro": True,
        "mensagem": "Entrada validada sem padrões suspeitos.",
        "valor_recebido": valor,
    }


@router.get("/exemplo-mascaramento")
def exemplo_mascaramento():
    """Demonstra como dados sensíveis são mascarados antes de exposição."""
    dados_exemplo = {
        "nome": "Cliente Exemplo",
        "cpf": "123.456.789-00",
        "email": "cliente.exemplo@email.com",
        "numero_cartao": "4111111111111111",
        "cvv": "123",
        "agencia": {
            "numero": "0001",
            "endereco": "Rua Exemplo, 100",
        },
    }
    return mascarar_dados_sensiveis(dados_exemplo)
