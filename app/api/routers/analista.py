from typing import Optional

from fastapi import APIRouter, Query
import sqlite3

<<<<<<< HEAD
from app.services.fraude_service import (
    desbloquear_conta_manual,
    inicializar_tabelas_fraude,
    linha_para_dict,
    processar_todas_transacoes,
)

=======
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b
router = APIRouter(prefix="/analista", tags=["Painel do Analista (US04)"])

DB_PATH = "data/banco_brasil_transacoes.sqlite"


# ── ENDPOINTS ORIGINAIS (US04) ──────────────────────────────────────────────

@router.get("/contas-bloqueadas")
def listar_bloqueios():
<<<<<<< HEAD
    conn = conectar_banco()
    inicializar_tabelas_fraude(conn)
    rows = conn.execute("SELECT * FROM contas_bloqueadas WHERE status = 'Bloqueada' ORDER BY id DESC").fetchall()
    conn.close()
    return {"bloqueadas": [linha_para_dict(row) for row in rows]}


@router.post("/desbloquear/{conta}")
def desbloquear_conta(conta: str, justificativa: str = "Desbloqueio manual pelo analista", analista: str = "Analista"):
    conn = conectar_banco()
    desbloquear_conta_manual(conn, conta, justificativa, analista)
    conn.commit()
    conn.close()
    return {"mensagem": f"Conta {conta} desbloqueada manualmente."}
=======
    # Lista de contas suspensas por risco 3
    return {"bloqueadas": []}


@router.post("/desbloquear/{conta_id}")
def desbloquear_conta(conta_id: int):
    # Função para o analista reativar conta.
    return {"mensagem": f"Conta {conta_id} desbloqueada manualmente."}
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b


# ── HELPERS ────────────────────────────────────────────────────────────────

def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def colunas_transactions(conn) -> set[str]:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    return {linha[1] for linha in cursor.fetchall()}


# ── DASHBOARD DO ANALISTA (3.1) ─────────────────────────────────────────────

@router.get("/resumo")
def resumo_movimentacoes():
    """Retorna um resumo completo das movimentações para o painel do analista."""
    conn = conectar_banco()
<<<<<<< HEAD
    inicializar_tabelas_fraude(conn)
    processar_todas_transacoes(conn)
=======
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(valor), 0) AS volume,
            COALESCE(AVG(valor), 0) AS media,
            COALESCE(MAX(valor), 0) AS maior
        FROM transactions
        """
    )
    kpis = dict(cursor.fetchone())

    cursor.execute(
        """
        SELECT COUNT(*) AS total_anomalias
        FROM transactions
<<<<<<< HEAD
        WHERE classificacao_risco IN ('amarelo', 'vermelho')
=======
        WHERE valor > 5000 OR hora BETWEEN '00:00' AND '05:59'
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b
        """
    )
    kpis["total_anomalias"] = cursor.fetchone()["total_anomalias"]

    cursor.execute(
        """
        SELECT categoria, COUNT(*) AS qtd, COALESCE(SUM(valor), 0) AS volume
        FROM transactions
        GROUP BY categoria
        ORDER BY volume DESC
        """
    )
    por_categoria = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT cidade, COUNT(*) AS qtd, COALESCE(SUM(valor), 0) AS volume
        FROM transactions
        GROUP BY cidade
        ORDER BY volume DESC
        LIMIT 10
        """
    )
    por_cidade = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT dispositivo, COUNT(*) AS qtd
        FROM transactions
        GROUP BY dispositivo
        ORDER BY qtd DESC
        """
    )
    por_dispositivo = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT tipo_transacao, COUNT(*) AS qtd, COALESCE(SUM(valor), 0) AS volume
        FROM transactions
        GROUP BY tipo_transacao
        ORDER BY volume DESC
        """
    )
    por_tipo = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT SUBSTR(hora, 1, 2) AS hora_dia, COUNT(*) AS qtd, COALESCE(SUM(valor), 0) AS volume
        FROM transactions
        GROUP BY hora_dia
        ORDER BY hora_dia
        """
    )
    por_hora = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 10")
    ultimas_transacoes = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "kpis": kpis,
        "por_categoria": por_categoria,
        "por_cidade": por_cidade,
        "por_dispositivo": por_dispositivo,
        "por_tipo": por_tipo,
        "por_hora": por_hora,
        "ultimas_transacoes": ultimas_transacoes,
    }


@router.get("/anomalias-detalhadas")
def anomalias_detalhadas():
    """Lista as anomalias com a regra que as identificou."""
    conn = conectar_banco()
<<<<<<< HEAD
    inicializar_tabelas_fraude(conn)
    processar_todas_transacoes(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *, motivo_risco AS regra_alerta
        FROM transactions
        WHERE classificacao_risco IN ('amarelo', 'vermelho')
        ORDER BY id DESC
=======
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *,
            CASE
                WHEN valor > 10000 THEN 'Valor Muito Alto (>R$10.000)'
                WHEN hora BETWEEN '00:00' AND '05:59' THEN 'Horário Suspeito (Madrugada)'
                WHEN dispositivo = 'caixa_eletronico' AND valor > 5000 THEN 'Saque Alto em Caixa Eletrônico'
                ELSE 'Valor Alto (>R$5.000)'
            END AS regra_alerta
        FROM transactions
        WHERE valor > 5000 OR hora BETWEEN '00:00' AND '05:59'
        ORDER BY valor DESC
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b
        LIMIT 50
        """
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ── FILTROS AVANÇADOS DO DASHBOARD (3.5) ───────────────────────────────────

@router.get("/categorias")
def listar_categorias():
    """Retorna as categorias disponíveis para preencher o filtro do dashboard."""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM transactions ORDER BY categoria")
    categorias = [row["categoria"] for row in cursor.fetchall()]
    conn.close()
    return {"categorias": categorias}


@router.get("/transacoes-filtradas")
def transacoes_filtradas(
    cpf: Optional[str] = Query(None, description="CPF do cliente. Se a base não tiver CPF, o filtro é aplicado na conta."),
    conta: Optional[str] = Query(None, description="Conta bancária."),
    categoria: Optional[str] = Query(None, description="Categoria da transação."),
    valor_min: Optional[float] = Query(None, ge=0, description="Valor mínimo da transação."),
    valor_max: Optional[float] = Query(None, ge=0, description="Valor máximo da transação."),
    limite: int = Query(100, ge=1, le=500, description="Quantidade máxima de registros retornados."),
):
    """Filtra transações por CPF/conta, categoria e faixa de valor."""
    conn = conectar_banco()
<<<<<<< HEAD
    inicializar_tabelas_fraude(conn)
    processar_todas_transacoes(conn)
=======
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b
    cursor = conn.cursor()
    colunas = colunas_transactions(conn)

    filtros = []
    parametros = []
    avisos = []

    if cpf:
        if "cpf" in colunas:
            filtros.append("cpf LIKE ?")
            parametros.append(f"%{cpf}%")
        elif "conta" in colunas:
            filtros.append("conta LIKE ?")
            parametros.append(f"%{cpf}%")
            avisos.append("A base atual não possui coluna CPF; o filtro foi aplicado no campo conta.")
        else:
            avisos.append("A base atual não possui coluna CPF nem conta para aplicar esse filtro.")

    if conta and "conta" in colunas:
        filtros.append("conta LIKE ?")
        parametros.append(f"%{conta}%")

    if categoria:
        filtros.append("LOWER(categoria) = LOWER(?)")
        parametros.append(categoria)

    if valor_min is not None:
        filtros.append("valor >= ?")
        parametros.append(valor_min)

    if valor_max is not None:
        filtros.append("valor <= ?")
        parametros.append(valor_max)

    where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    cursor.execute(f"SELECT COUNT(*) AS total FROM transactions {where_sql}", parametros)
    total = cursor.fetchone()["total"]

    cursor.execute(
        f"""
        SELECT *
        FROM transactions
        {where_sql}
        ORDER BY id DESC
        LIMIT ?
        """,
        [*parametros, limite],
    )
    transacoes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "total": total,
        "limite": limite,
        "transacoes": transacoes,
        "avisos": avisos,
    }


# ROUTER (US04)
