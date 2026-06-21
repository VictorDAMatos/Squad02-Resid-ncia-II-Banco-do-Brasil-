"""Camadas de seguranca para a API.

Implementa protecoes nao invasivas para os endpoints existentes:
- validacao de parametros contra padroes comuns de SQL Injection;
- headers HTTP de seguranca;
- helpers para mascaramento de dados sensiveis.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


PADROES_SQL_INJECTION = [
    r"\bunion\b\s+\bselect\b",
    r"\bselect\b.+\bfrom\b",
    r"\binsert\b\s+\binto\b",
    r"\bupdate\b.+\bset\b",
    r"\bdelete\b\s+\bfrom\b",
    r"\bdrop\b\s+\b(table|database)\b",
    r"\balter\b\s+\btable\b",
    r"\btruncate\b\s+\btable\b",
    r"\bexec\b|\bexecute\b",
    r"\bsleep\s*\(",
    r"\bpragma\b",
    r"(--|#|/\*|\*/)",
    r"\b(or|and)\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
    r";\s*(drop|delete|insert|update|select|alter|truncate)\b",
]

CAMPOS_SENSIVEIS = {
    "cpf",
    "cnpj",
    "email",
    "telefone",
    "endereco",
    "numero_cartao",
    "cartao",
    "cvv",
    "senha",
    "password",
    "token",
}


def _normalizar_texto(valor: str) -> str:
    return " ".join(valor.strip().lower().split())


def contem_padrao_suspeito(valor: Any) -> bool:
    """Detecta padroes comuns de tentativa de injecao em valores textuais."""
    if valor is None:
        return False

    texto = _normalizar_texto(str(valor))
    if not texto:
        return False

    return any(re.search(padrao, texto, re.IGNORECASE | re.DOTALL) for padrao in PADROES_SQL_INJECTION)


def mascarar_cpf(cpf: str | None) -> str | None:
    if not cpf:
        return cpf
    digitos = re.sub(r"\D", "", str(cpf))
    if len(digitos) < 5:
        return "***"
    return f"***.{digitos[-5:-2]}.{digitos[-2:]}"


def mascarar_email(email: str | None) -> str | None:
    if not email or "@" not in str(email):
        return email
    usuario, dominio = str(email).split("@", 1)
    prefixo = usuario[:2] if len(usuario) >= 2 else usuario[:1]
    return f"{prefixo}***@{dominio}"


def mascarar_numero(valor: str | None) -> str | None:
    if not valor:
        return valor
    texto = str(valor)
    digitos = re.sub(r"\D", "", texto)
    if len(digitos) <= 4:
        return "****"
    return f"****{digitos[-4:]}"


def mascarar_dados_sensiveis(dados: Any) -> Any:
    """Mascara dados sensiveis em dicts/listas sem alterar a estrutura da resposta."""
    if isinstance(dados, list):
        return [mascarar_dados_sensiveis(item) for item in dados]

    if isinstance(dados, dict):
        resultado = {}
        for chave, valor in dados.items():
            chave_normalizada = str(chave).lower()
            if chave_normalizada in {"cpf", "cnpj"}:
                resultado[chave] = mascarar_cpf(str(valor))
            elif chave_normalizada == "email":
                resultado[chave] = mascarar_email(str(valor))
            elif chave_normalizada in {"numero_cartao", "cartao", "cvv", "senha", "password", "token"}:
                resultado[chave] = mascarar_numero(str(valor))
            elif chave_normalizada in CAMPOS_SENSIVEIS:
                resultado[chave] = "***"
            else:
                resultado[chave] = mascarar_dados_sensiveis(valor)
        return resultado

    return dados


class ProtecaoRequisicaoMiddleware(BaseHTTPMiddleware):
    """Bloqueia parametros suspeitos antes de chegarem aos endpoints."""

    async def dispatch(self, request: Request, call_next):
        valores_para_validar = [request.url.path]
        valores_para_validar.extend(valor for _, valor in request.query_params.multi_items())

        for valor in valores_para_validar:
            if contem_padrao_suspeito(valor):
                return JSONResponse(
                    status_code=400,
                    content={
                        "erro": "Requisicao bloqueada pela camada de seguranca.",
                        "motivo": "Parametro com padrao suspeito de SQL Injection ou comando perigoso.",
                    },
                )

        return await call_next(request)


class HeadersSegurancaMiddleware(BaseHTTPMiddleware):
    """Adiciona headers de protecao nas respostas HTTP."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault("Cache-Control", "no-store")
        return response


def configurar_camadas_de_seguranca(app) -> None:
    """Registra as camadas globais de seguranca da API."""
    app.add_middleware(HeadersSegurancaMiddleware)
    app.add_middleware(ProtecaoRequisicaoMiddleware)

import os
import secrets
from fastapi import Header, HTTPException, status


DEFAULT_DEV_TOKEN = "analista-dev-token"


def verificar_analista(x_analista_token: str | None = Header(default=None)):
    """
    Verifica se a requisição possui token de analista.

    Em ambiente de desenvolvimento, é possível desativar essa checagem
    usando a variável de ambiente:
    ANALISTA_AUTH_DISABLED=true
    """

    auth_desativada = os.getenv("ANALISTA_AUTH_DISABLED", "false").strip().lower()

    if auth_desativada in {"1", "true", "sim", "yes", "on"}:
        return {
            "perfil": "analista",
            "autenticado": False,
            "modo": "auth_desativada"
        }

    token_esperado = os.getenv("ANALISTA_API_TOKEN", DEFAULT_DEV_TOKEN)

    if not x_analista_token or not secrets.compare_digest(x_analista_token, token_esperado):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso exclusivo do analista. Envie um X-Analista-Token válido.",
        )

    return {
        "perfil": "analista",
        "autenticado": True
    }
