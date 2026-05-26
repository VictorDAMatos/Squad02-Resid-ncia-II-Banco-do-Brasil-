from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import sqlite3

router = APIRouter(prefix="/analise", tags=["Análise Manual 4.1 a 4.12"])

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"


class AcaoAnalise(BaseModel):
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


class BloqueioConta(BaseModel):
    conta: str = Field(..., min_length=1)
    transacao_id: int = Field(..., gt=0)
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


class DesbloqueioConta(BaseModel):
    conta: str = Field(..., min_length=1)
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


class InjecaoSaldo(BaseModel):
    conta: str = Field(..., min_length=1)
    valor: float = Field(..., gt=0)
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(DB_PATH, timeout=10)
    conexao.row_factory = sqlite3.Row
    return conexao


def tabela_existe(conexao: sqlite3.Connection, nome: str) -> bool:
    row = conexao.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (nome,),
    ).fetchone()
    return row is not None


def inicializar_tabelas() -> None:
    with conectar() as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS analise_casos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transacao_id INTEGER NOT NULL UNIQUE,
                conta TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pendente',
                resultado TEXT,
                risco_nivel TEXT,
                risco_pontos INTEGER,
                aberto_em TEXT NOT NULL,
                atualizado_em TEXT,
                analista TEXT,
                detalhe TEXT
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS contas_bloqueadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conta TEXT NOT NULL UNIQUE,
                titular TEXT,
                motivo TEXT NOT NULL,
                transacao_id INTEGER,
                data_hora TEXT NOT NULL,
                analista TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Bloqueada'
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS logs_justificativas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                analista TEXT NOT NULL,
                acao TEXT NOT NULL,
                justificativa TEXT NOT NULL,
                transacao_id INTEGER,
                conta TEXT
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS logs_notificacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                tipo TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Enviada',
                transacao_id INTEGER,
                conta TEXT
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS saldo_injecoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                conta TEXT NOT NULL,
                valor REAL NOT NULL,
                justificativa TEXT NOT NULL,
                analista TEXT NOT NULL,
                aplicado_na_tabela_conta INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conexao.commit()


def linha_para_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


def buscar_transacao(conexao: sqlite3.Connection, transacao_id: int) -> dict:
    row = conexao.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transacao_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return linha_para_dict(row)


def calcular_risco(transacao: dict) -> dict:
    valor = float(transacao.get("valor") or 0)
    hora = str(transacao.get("hora") or "00:00")
    dispositivo = str(transacao.get("dispositivo") or "").lower()

    pontos = 0
    motivos = []

    if valor > 10000:
        pontos += 40
        motivos.append("valor extremo")
    elif valor > 5000:
        pontos += 25
        motivos.append("valor alto")
    elif valor > 3000:
        pontos += 15
        motivos.append("valor acima do padrão")

    if "00:00" <= hora <= "05:59":
        pontos += 30
        motivos.append("operação de madrugada")
    elif hora >= "23:00" or hora <= "06:59":
        pontos += 15
        motivos.append("horário incomum")

    if dispositivo == "caixa_eletronico" and valor >= 5000:
        pontos += 20
        motivos.append("saque alto em caixa eletrônico")
    elif dispositivo not in {"app_mobile", "web", "internet_banking", "caixa_eletronico"}:
        pontos += 10
        motivos.append("dispositivo fora do padrão")

    if pontos <= 30:
        nivel = "Baixo"
        classe = "baixo"
    elif pontos <= 70:
        nivel = "Médio"
        classe = "medio"
    else:
        nivel = "Alto"
        classe = "alto"

    return {
        "pontos": pontos,
        "nivel": nivel,
        "classe": classe,
        "motivos": motivos or ["sem indícios fortes"],
    }


def registrar_justificativa(
    conexao: sqlite3.Connection,
    acao: str,
    justificativa: str,
    analista: str,
    transacao_id: Optional[int] = None,
    conta: Optional[str] = None,
) -> None:
    conexao.execute(
        """
        INSERT INTO logs_justificativas
            (data_hora, analista, acao, justificativa, transacao_id, conta)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (agora(), analista, acao, justificativa, transacao_id, conta),
    )


def registrar_notificacao(
    conexao: sqlite3.Connection,
    tipo: str,
    mensagem: str,
    transacao_id: Optional[int] = None,
    conta: Optional[str] = None,
) -> None:
    conexao.execute(
        """
        INSERT INTO logs_notificacoes
            (data_hora, tipo, mensagem, status, transacao_id, conta)
        VALUES (?, ?, ?, 'Enviada', ?, ?)
        """,
        (agora(), tipo, mensagem, transacao_id, conta),
    )


def garantir_caso(conexao: sqlite3.Connection, transacao: dict) -> None:
    risco = calcular_risco(transacao)
    if risco["nivel"] == "Baixo":
        return

    conexao.execute(
        """
        INSERT OR IGNORE INTO analise_casos
            (transacao_id, conta, status, risco_nivel, risco_pontos, aberto_em, detalhe)
        VALUES (?, ?, 'Pendente', ?, ?, ?, ?)
        """,
        (
            transacao["id"],
            transacao.get("conta"),
            risco["nivel"],
            risco["pontos"],
            agora(),
            ", ".join(risco["motivos"]),
        ),
    )


def atualizar_caso(
    conexao: sqlite3.Connection,
    transacao: dict,
    status: str,
    resultado: str,
    analista: str,
    detalhe: str,
) -> None:
    risco = calcular_risco(transacao)
    garantir_caso(conexao, transacao)
    conexao.execute(
        """
        UPDATE analise_casos
        SET status = ?, resultado = ?, risco_nivel = ?, risco_pontos = ?,
            atualizado_em = ?, analista = ?, detalhe = ?
        WHERE transacao_id = ?
        """,
        (
            status,
            resultado,
            risco["nivel"],
            risco["pontos"],
            agora(),
            analista,
            detalhe,
            transacao["id"],
        ),
    )


def status_da_transacao(conexao: sqlite3.Connection, transacao_id: int) -> str:
    row = conexao.execute(
        "SELECT status FROM analise_casos WHERE transacao_id = ?",
        (transacao_id,),
    ).fetchone()
    return row["status"] if row else "Pendente"


def conta_esta_bloqueada(conexao: sqlite3.Connection, conta: str) -> bool:
    row = conexao.execute(
        "SELECT id FROM contas_bloqueadas WHERE conta = ? AND status = 'Bloqueada'",
        (conta,),
    ).fetchone()
    return row is not None


def enriquecer_transacao(conexao: sqlite3.Connection, transacao: dict) -> dict:
    item = dict(transacao)
    item["risco"] = calcular_risco(transacao)
    item["status_analise"] = status_da_transacao(conexao, transacao["id"])
    item["conta_bloqueada"] = conta_esta_bloqueada(conexao, transacao.get("conta"))
    return item


def montar_perfil_dispositivo(conexao: sqlite3.Connection, conta: Optional[str] = None) -> list[dict]:
    params = []
    filtro = ""
    if conta:
        filtro = "WHERE conta = ?"
        params.append(conta)

    rows = conexao.execute(
        f"""
        SELECT conta, dispositivo, cidade,
               COUNT(*) AS total_uso,
               MIN(data || ' ' || hora) AS primeiro_uso,
               MAX(data || ' ' || hora) AS ultimo_uso,
               AVG(valor) AS valor_medio,
               MAX(valor) AS maior_valor
        FROM transactions
        {filtro}
        GROUP BY conta, dispositivo, cidade
        ORDER BY total_uso DESC, maior_valor DESC
        LIMIT 100
        """,
        params,
    ).fetchall()

    perfis = []
    for row in rows:
        item = linha_para_dict(row)
        if item["total_uso"] >= 5:
            confiavel = "Sim"
        elif item["total_uso"] >= 2:
            confiavel = "Parcial"
        else:
            confiavel = "Não"
        item["confiavel"] = confiavel
        perfis.append(item)
    return perfis


@router.get("/dashboard")
def dashboard():
    inicializar_tabelas()
    with conectar() as conexao:
        total_transacoes = conexao.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        total_bloqueadas = conexao.execute("SELECT COUNT(*) FROM contas_bloqueadas WHERE status = 'Bloqueada'").fetchone()[0]
        total_notificacoes = conexao.execute("SELECT COUNT(*) FROM logs_notificacoes").fetchone()[0]
        sla_rows = conexao.execute(
            """
            SELECT aberto_em, atualizado_em
            FROM analise_casos
            WHERE atualizado_em IS NOT NULL
            """
        ).fetchall()

        tempos = []
        for row in sla_rows:
            inicio = datetime.fromisoformat(row["aberto_em"])
            fim = datetime.fromisoformat(row["atualizado_em"])
            tempos.append(max(1, round((fim - inicio).total_seconds() / 60)))

    sla_medio = round(sum(tempos) / len(tempos)) if tempos else 0
    return {
        "totalTransacoes": total_transacoes,
        "totalBloqueadas": total_bloqueadas,
        "totalNotificacoes": total_notificacoes,
        "slaMedio": sla_medio,
    }


@router.get("/transacoes")
def listar_transacoes(
    risco: str = Query("Todos", pattern="^(Todos|Baixo|Médio|Medio|Alto)$"),
    limite: int = Query(100, ge=1, le=500),
):
    inicializar_tabelas()
    risco_normalizado = "Médio" if risco == "Medio" else risco

    with conectar() as conexao:
        rows = conexao.execute(
            "SELECT * FROM transactions ORDER BY id DESC LIMIT ?",
            (limite,),
        ).fetchall()

        resultado = []
        for row in rows:
            transacao = linha_para_dict(row)
            risco_transacao = calcular_risco(transacao)
            if risco_normalizado != "Todos" and risco_transacao["nivel"] != risco_normalizado:
                continue
            garantir_caso(conexao, transacao)
            resultado.append(enriquecer_transacao(conexao, transacao))

        conexao.commit()

    return {"total": len(resultado), "transacoes": resultado}


@router.get("/transacoes/{transacao_id}")
def visualizar_transacao(transacao_id: int):
    inicializar_tabelas()
    with conectar() as conexao:
        transacao = buscar_transacao(conexao, transacao_id)
        garantir_caso(conexao, transacao)
        item = enriquecer_transacao(conexao, transacao)
        item["perfil_dispositivo"] = montar_perfil_dispositivo(conexao, transacao.get("conta"))
        conexao.commit()
    return item


@router.post("/transacoes/{transacao_id}/confirmar")
def confirmar_suspeita(transacao_id: int, dados: AcaoAnalise):
    inicializar_tabelas()
    with conectar() as conexao:
        transacao = buscar_transacao(conexao, transacao_id)
        atualizar_caso(
            conexao,
            transacao,
            status="Confirmada como suspeita",
            resultado="Confirmada",
            analista=dados.analista,
            detalhe=dados.justificativa,
        )
        registrar_justificativa(conexao, "Confirmação de suspeita", dados.justificativa, dados.analista, transacao_id, transacao.get("conta"))
        registrar_notificacao(conexao, "Alerta", f"Transação {transacao_id} confirmada como suspeita.", transacao_id, transacao.get("conta"))
        conexao.commit()
    return {"mensagem": "Transação confirmada como suspeita"}


@router.post("/transacoes/{transacao_id}/aprovar")
def aprovar_transacao(transacao_id: int, dados: AcaoAnalise):
    inicializar_tabelas()
    with conectar() as conexao:
        transacao = buscar_transacao(conexao, transacao_id)
        atualizar_caso(
            conexao,
            transacao,
            status="Aprovada",
            resultado="Aprovada",
            analista=dados.analista,
            detalhe=dados.justificativa,
        )
        registrar_justificativa(conexao, "Aprovação manual", dados.justificativa, dados.analista, transacao_id, transacao.get("conta"))
        registrar_notificacao(conexao, "Aprovação", f"Transação {transacao_id} aprovada manualmente.", transacao_id, transacao.get("conta"))
        conexao.commit()
    return {"mensagem": "Transação aprovada manualmente"}


@router.post("/contas/bloquear")
def bloquear_conta(dados: BloqueioConta):
    inicializar_tabelas()
    with conectar() as conexao:
        transacao = buscar_transacao(conexao, dados.transacao_id)
        if str(transacao.get("conta")) != dados.conta:
            raise HTTPException(status_code=400, detail="A conta informada não corresponde à transação")

        conexao.execute(
            """
            INSERT INTO contas_bloqueadas
                (conta, titular, motivo, transacao_id, data_hora, analista, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Bloqueada')
            ON CONFLICT(conta) DO UPDATE SET
                motivo = excluded.motivo,
                transacao_id = excluded.transacao_id,
                data_hora = excluded.data_hora,
                analista = excluded.analista,
                status = 'Bloqueada'
            """,
            (dados.conta, dados.conta, dados.justificativa, dados.transacao_id, agora(), dados.analista),
        )
        atualizar_caso(
            conexao,
            transacao,
            status="Conta bloqueada",
            resultado="Bloqueada",
            analista=dados.analista,
            detalhe=dados.justificativa,
        )
        registrar_justificativa(conexao, "Bloqueio de conta", dados.justificativa, dados.analista, dados.transacao_id, dados.conta)
        registrar_notificacao(conexao, "Bloqueio", f"Conta {dados.conta} bloqueada.", dados.transacao_id, dados.conta)
        conexao.commit()
    return {"mensagem": "Conta bloqueada com sucesso"}


@router.get("/contas/bloqueadas")
def listar_contas_bloqueadas():
    inicializar_tabelas()
    with conectar() as conexao:
        rows = conexao.execute(
            "SELECT * FROM contas_bloqueadas WHERE status = 'Bloqueada' ORDER BY id DESC"
        ).fetchall()
    return {"bloqueadas": [linha_para_dict(row) for row in rows]}


@router.post("/contas/desbloquear")
def desbloquear_conta(dados: DesbloqueioConta):
    inicializar_tabelas()
    with conectar() as conexao:
        bloqueio = conexao.execute(
            "SELECT * FROM contas_bloqueadas WHERE conta = ? AND status = 'Bloqueada'",
            (dados.conta,),
        ).fetchone()
        if not bloqueio:
            raise HTTPException(status_code=404, detail="Conta bloqueada não encontrada")

        conexao.execute(
            "UPDATE contas_bloqueadas SET status = 'Desbloqueada' WHERE conta = ?",
            (dados.conta,),
        )
        registrar_justificativa(conexao, "Desbloqueio de conta", dados.justificativa, dados.analista, bloqueio["transacao_id"], dados.conta)
        registrar_notificacao(conexao, "Desbloqueio", f"Conta {dados.conta} desbloqueada.", bloqueio["transacao_id"], dados.conta)
        conexao.commit()
    return {"mensagem": "Conta desbloqueada com sucesso"}


@router.post("/saldo/injetar")
def injetar_saldo(dados: InjecaoSaldo):
    inicializar_tabelas()
    aplicado = 0
    with conectar() as conexao:
        if tabela_existe(conexao, "Conta"):
            atualizacao = conexao.execute(
                "UPDATE Conta SET saldo = saldo + ? WHERE numero = ?",
                (dados.valor, dados.conta),
            )
            aplicado = 1 if atualizacao.rowcount > 0 else 0

        conexao.execute(
            """
            INSERT INTO saldo_injecoes
                (data_hora, conta, valor, justificativa, analista, aplicado_na_tabela_conta)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (agora(), dados.conta, dados.valor, dados.justificativa, dados.analista, aplicado),
        )
        registrar_justificativa(
            conexao,
            "Injeção de saldo",
            f"Valor R$ {dados.valor:.2f}. Motivo: {dados.justificativa}",
            dados.analista,
            None,
            dados.conta,
        )
        registrar_notificacao(conexao, "Saldo", f"Saldo injetado/registrado na conta {dados.conta}.", None, dados.conta)
        conexao.commit()

    return {
        "mensagem": "Injeção de saldo registrada",
        "saldo_aplicado_na_tabela_conta": bool(aplicado),
    }


@router.get("/logs/justificativas")
def listar_justificativas(limite: int = Query(100, ge=1, le=500)):
    inicializar_tabelas()
    with conectar() as conexao:
        rows = conexao.execute(
            "SELECT * FROM logs_justificativas ORDER BY id DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return {"logs": [linha_para_dict(row) for row in rows]}


@router.get("/logs/notificacoes")
def listar_notificacoes(limite: int = Query(100, ge=1, le=500)):
    inicializar_tabelas()
    with conectar() as conexao:
        rows = conexao.execute(
            "SELECT * FROM logs_notificacoes ORDER BY id DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return {"logs": [linha_para_dict(row) for row in rows]}


@router.get("/dispositivos")
def listar_dispositivos(conta: Optional[str] = None):
    inicializar_tabelas()
    with conectar() as conexao:
        perfis = montar_perfil_dispositivo(conexao, conta)
    return {"dispositivos": perfis}


@router.get("/sla")
def listar_sla():
    inicializar_tabelas()
    with conectar() as conexao:
        rows = conexao.execute(
            "SELECT * FROM analise_casos ORDER BY id DESC"
        ).fetchall()

    casos = []
    for row in rows:
        caso = linha_para_dict(row)
        fim = caso.get("atualizado_em") or agora()
        inicio_dt = datetime.fromisoformat(caso["aberto_em"])
        fim_dt = datetime.fromisoformat(fim)
        tempo_minutos = max(1, round((fim_dt - inicio_dt).total_seconds() / 60))
        caso["tempo_minutos"] = tempo_minutos
        caso["sla_status"] = "Dentro do prazo" if tempo_minutos <= 30 else "Atrasado"
        casos.append(caso)

    return {"casos": casos}


@router.get("/timeline/{transacao_id}")
def listar_timeline_transacao(transacao_id: int):
    inicializar_tabelas()
    with conectar() as conexao:
        transacao = buscar_transacao(conexao, transacao_id)
        conta = transacao.get("conta")
        historico = conexao.execute(
            """
            SELECT id, data, hora, valor, categoria, cidade, tipo_transacao, dispositivo
            FROM transactions
            WHERE conta = ?
            ORDER BY data DESC, hora DESC
            LIMIT 10
            """,
            (conta,),
        ).fetchall()
        justificativas = conexao.execute(
            """
            SELECT data_hora, acao, justificativa
            FROM logs_justificativas
            WHERE transacao_id = ? OR conta = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (transacao_id, conta),
        ).fetchall()
        notificacoes = conexao.execute(
            """
            SELECT data_hora, tipo, mensagem, status
            FROM logs_notificacoes
            WHERE transacao_id = ? OR conta = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (transacao_id, conta),
        ).fetchall()

    eventos = [
        {
            "momento": f"{row['data']} {row['hora']}",
            "tipo": "Transação",
            "descricao": f"{row['tipo_transacao']} de R$ {row['valor']:.2f} em {row['cidade']} via {row['dispositivo']}.",
        }
        for row in historico
    ]
    eventos.extend(
        {
            "momento": row["data_hora"],
            "tipo": row["acao"],
            "descricao": row["justificativa"],
        }
        for row in justificativas
    )
    eventos.extend(
        {
            "momento": row["data_hora"],
            "tipo": row["tipo"],
            "descricao": f"{row['mensagem']} Status: {row['status']}.",
        }
        for row in notificacoes
    )

    return {
        "transacao": enriquecer_transacao(conectar(), transacao),
        "conta": conta,
        "eventos": eventos,
    }
