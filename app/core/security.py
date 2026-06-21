"""Proteção simples para rotas exclusivas do analista.

A integração com login/JWT do projeto principal pode substituir esta função depois.
Enquanto isso, as rotas do analista ficam protegidas por um token via header:

    X-Analista-Token: analista-dev-token

Em produção, configure a variável de ambiente ANALISTA_API_TOKEN com um valor secreto.
"""

import os
import secrets
from typing import Any

from fastapi import Header, HTTPException, status


DEFAULT_DEV_TOKEN = "analista-dev-token"


def verificar_analista(x_analista_token: str | None = Header(default=None)) -> dict[str, Any]:
    """Bloqueia acesso às rotas do analista quando o token não é válido.

    Variáveis úteis:
    - ANALISTA_API_TOKEN: token real usado em produção.
    - ANALISTA_AUTH_DISABLED=true: desativa temporariamente a proteção em ambiente local.
    """
    auth_desativada = os.getenv("ANALISTA_AUTH_DISABLED", "false").strip().lower()
    if auth_desativada in {"1", "true", "sim", "yes", "on"}:
        return {"perfil": "analista", "autenticado": False, "modo": "auth_desativada"}

    token_esperado = os.getenv("ANALISTA_API_TOKEN", DEFAULT_DEV_TOKEN)

    if not x_analista_token or not secrets.compare_digest(x_analista_token, token_esperado):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso exclusivo do analista. Envie um X-Analista-Token válido.",
        )

    return {"perfil": "analista", "autenticado": True}
