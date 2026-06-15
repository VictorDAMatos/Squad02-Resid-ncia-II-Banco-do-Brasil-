from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from app.schemas.ia_schema import TransacaoSchema
from app.services.fraude_service import (
    buscar_transacao,
    conectar,
    inicializar_tabelas_fraude,
    marcar_conta_bloqueada,
    registrar_notificacao,
)
from app.services.ia_service import (
    analisar_transacao_ia,
    aplicar_resultado_ia_na_transacao,
    status_final_ia,
)

router = APIRouter(prefix="/ia", tags=["🤖 IA & Motor Neural"])

@router.post("/analisar")
def analisar_transacao(transacao: TransacaoSchema):
    """Realiza a análise rápida de uma transação enviada diretamente via payload."""
    resultado = analisar_transacao_ia(transacao.model_dump())
    return {
        **resultado,
        "status_sugerido": status_final_ia(resultado["risco"]),
    }

@router.post("/analisar-anomalia")
def analisar_com_isolation_forest(transacao_id: int = Query(..., ge=1)):
    """Busca uma transação na base de dados pelo ID e aplica o motor Isolation Forest."""
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        transacao = buscar_transacao(conexao, transacao_id)

        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada.")

        resultado_ia = analisar_transacao_ia(transacao)
        decisao = aplicar_resultado_ia_na_transacao(
            conexao, transacao_id, resultado_ia, conta=transacao.get("conta")
        )

        if decisao["bloqueio_por_ia"]:
            marcar_conta_bloqueada(
                conexao,
                str(transacao.get("conta")),
                resultado_ia["motivo"],
                transacao_id,
                "IA - Isolation Forest",
            )
            registrar_notificacao(
                conexao,
                "Bloqueio por IA",
                f"Conta {transacao.get('conta')} bloqueada preventivamente por suspeita de fraude.",
                "alta",
            )

    return {
        **resultado_ia,
        "status_sugerido": status_final_ia(resultado_ia["risco"]),
        "decisao_final": decisao,
    }


@router.get("/relatorio-fraudes")
def gerar_relatorio_ia():
    """Gera um relatório estatístico detalhado focado em fraudes e score médio."""
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        row = conexao.execute(
            """
            SELECT
                COUNT(*) AS total_transacoes,
                COALESCE(SUM(CASE WHEN ia_risco = 1 THEN 1 ELSE 0 END), 0) AS risco_1,
                COALESCE(SUM(CASE WHEN ia_risco = 2 THEN 1 ELSE 0 END), 0) AS risco_2,
                COALESCE(SUM(CASE WHEN ia_risco = 3 THEN 1 ELSE 0 END), 0) AS risco_3,
                COALESCE(AVG(ia_score), 0) AS score_medio,
                COALESCE(SUM(CASE WHEN ia_anomalia = 1 THEN 1 ELSE 0 END), 0) AS anomalias_detectadas
            FROM transactions
            """
        ).fetchone()

        por_categoria = conexao.execute(
            """
            SELECT categoria, COUNT(*) AS quantidade, COALESCE(AVG(ia_score), 0) AS score_medio
            FROM transactions
            GROUP BY categoria
            ORDER BY quantidade DESC
            """
        ).fetchall()

    total = row["total_transacoes"] or 0
    return {
        "resumo": dict(row),
        "taxa_anomalia_percentual": round((row["anomalias_detectadas"] / total) * 100, 2) if total else 0,
        "distribuicao_por_categoria": [dict(cat) for cat in por_categoria],
    }

@router.get("/dashboard")
def dashboard_ia():
    """Retorna dados agregados de volumetria de anomalias para painéis gráficos."""
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        row = conexao.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN ia_risco = 2 THEN 1 ELSE 0 END), 0) AS suspeitas,
                COALESCE(SUM(CASE WHEN ia_risco = 3 THEN 1 ELSE 0 END), 0) AS bloqueadas,
                COALESCE(SUM(CASE WHEN ia_anomalia = 1 THEN 1 ELSE 0 END), 0) AS anomalias
            FROM transactions
            """
        ).fetchone()

    total = row["total"] or 0
    return {
        "total_transacoes": total,
        "suspeitas": row["suspeitas"],
        "bloqueadas": row["bloqueadas"],
        "anomalias": row["anomalias"],
        "taxa_fraude": round((row["bloqueadas"] / total) * 100, 2) if total else 0,
    }

@router.get("/anomalies")
def listar_anomalias(limite: int = Query(100, ge=1, le=1000)):
    """Lista transações consideradas anomalias ou de alto risco com base em múltiplos critérios."""
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        rows = conexao.execute(
            """
            SELECT *
            FROM transactions
            WHERE
                ia_anomalia = 1
                OR ia_risco >= 2
                OR classificacao_risco IN ('amarelo', 'vermelho')
                OR valor > 5000
                OR hora BETWEEN '00:00' AND '05:59'
            ORDER BY COALESCE(ia_risco, 1) DESC, valor DESC, id DESC
            LIMIT ?
            """,
            (limite,),
        ).fetchall()
    return [dict(row) for row in rows]