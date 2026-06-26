from __future__ import annotations

from datetime import datetime
from typing import Any

from app.ai.inference.predictor import prever


def analisar_transacao_ia(transacao: dict[str, Any]) -> dict[str, Any]:
    resultado = prever(transacao)
    return {
        "risco": int(resultado["risco"]),
        "score": float(resultado["score"]),
        "anomalia": bool(resultado["anomalia"]),
        "motivo": str(resultado["motivo"]),
    }


def classificacao_por_risco_ia(risco: int) -> str:
    if risco >= 3:
        return "vermelho"
    if risco == 2:
        return "amarelo"
    return "verde"


def status_por_risco_ia(risco: int) -> str:
    if risco >= 3:
        return "pendente"
    if risco == 2:
        return "em análise"
    return "aprovada"


def status_final_ia(risco: int) -> str:
    if risco >= 3:
        return "BLOQUEADA"
    if risco == 2:
        return "EM_ANALISE"
    return "APROVADA"


def severidade_classificacao(classificacao: str | None) -> int:
    mapa = {"verde": 1, "amarelo": 2, "vermelho": 3}
    return mapa.get(str(classificacao or "").lower(), 0)


def aplicar_resultado_ia_na_transacao(conexao, transacao_id: int, resultado_ia: dict[str, Any], conta: str | None = None) -> dict[str, Any]:
    """Salva os campos de IA e eleva o risco final quando a IA for mais crítica.

    A regra foi feita para preservar o motor de risco existente: se a regra manual
    já classificou a transação como mais grave, ela permanece. Se a IA encontrar
    risco maior, a classificação e status finais são elevados.
    """
    risco_ia = int(resultado_ia.get("risco") or 1)
    classificacao_ia = classificacao_por_risco_ia(risco_ia)
    status_transacao_ia = status_por_risco_ia(risco_ia)

    row = conexao.execute(
        "SELECT classificacao_risco, motivo_risco, status_transacao, conta FROM transactions WHERE id = ?",
        (transacao_id,),
    ).fetchone()
    atual = dict(row) if row else {}

    classificacao_atual = atual.get("classificacao_risco") or "verde"
    status_atual = atual.get("status_transacao") or "aprovada"
    motivo_atual = atual.get("motivo_risco") or "transação dentro dos parâmetros normais"
    conta_final = conta or atual.get("conta")

    if severidade_classificacao(classificacao_ia) > severidade_classificacao(classificacao_atual):
        classificacao_final = classificacao_ia
        status_final = status_transacao_ia
        motivo_final = resultado_ia.get("motivo") or motivo_atual
    else:
        classificacao_final = classificacao_atual
        status_final = status_atual
        motivo_final = motivo_atual

    conexao.execute(
        """
        UPDATE transactions
        SET ia_anomalia = ?, ia_score = ?, ia_risco = ?, ia_motivo = ?,
            classificacao_risco = ?, motivo_risco = ?, status_transacao = ?, ia_processado_em = ?
        WHERE id = ?
        """,
        (
            1 if resultado_ia.get("anomalia") else 0,
            float(resultado_ia.get("score") or 0),
            risco_ia,
            resultado_ia.get("motivo"),
            classificacao_final,
            motivo_final,
            status_final,
            datetime.now().isoformat(timespec="seconds"),
            transacao_id,
        ),
    )

    bloqueio_por_ia = risco_ia >= 3
    if bloqueio_por_ia and conta_final:
        conexao.execute("UPDATE transactions SET status_conta = 'Bloqueada' WHERE conta = ?", (conta_final,))

    return {
        "classificacao_final": classificacao_final,
        "status_transacao_final": status_final,
        "bloqueio_por_ia": bloqueio_por_ia,
        "status_ia": status_final_ia(risco_ia),
    }
