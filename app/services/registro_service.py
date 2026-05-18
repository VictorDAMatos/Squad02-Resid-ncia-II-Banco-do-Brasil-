import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"


def _agora_iso() -> str:
    """Retorna a data/hora atual em formato ISO para padronizar os registros."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(DB_PATH, timeout=10)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_tabelas_registro() -> None:
    """Cria as tabelas de logs e auditoria sem apagar ou alterar os dados existentes."""
    with _conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs_operacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                metodo TEXT NOT NULL,
                rota TEXT NOT NULL,
                query_params TEXT,
                status_code INTEGER,
                tempo_ms REAL,
                ip_origem TEXT,
                user_agent TEXT,
                detalhe TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS registros_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                ator_id TEXT NOT NULL DEFAULT 'sistema',
                ator_nome TEXT NOT NULL DEFAULT 'Sistema',
                acao TEXT NOT NULL,
                recurso TEXT NOT NULL,
                metodo TEXT NOT NULL,
                status_code INTEGER,
                ip_origem TEXT,
                detalhe TEXT
            )
            """
        )
        conexao.commit()


def registrar_log_operacao(
    *,
    metodo: str,
    rota: str,
    query_params: Optional[str] = None,
    status_code: Optional[int] = None,
    tempo_ms: Optional[float] = None,
    ip_origem: Optional[str] = None,
    user_agent: Optional[str] = None,
    detalhe: Optional[str] = None,
) -> None:
    """Registra o histórico técnico de uma operação executada na API."""
    inicializar_tabelas_registro()
    with _conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO logs_operacoes
                (data_hora, metodo, rota, query_params, status_code, tempo_ms, ip_origem, user_agent, detalhe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _agora_iso(),
                metodo.upper(),
                rota,
                query_params,
                status_code,
                tempo_ms,
                ip_origem,
                user_agent,
                detalhe,
            ),
        )
        conexao.commit()


def registrar_auditoria(
    *,
    ator_id: Optional[str],
    ator_nome: Optional[str],
    acao: str,
    recurso: str,
    metodo: str,
    status_code: Optional[int] = None,
    ip_origem: Optional[str] = None,
    detalhe: Optional[str] = None,
) -> None:
    """Registra quem executou uma ação relevante dentro do sistema."""
    inicializar_tabelas_registro()
    with _conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO registros_auditoria
                (data_hora, ator_id, ator_nome, acao, recurso, metodo, status_code, ip_origem, detalhe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _agora_iso(),
                ator_id or "sistema",
                ator_nome or "Sistema",
                acao,
                recurso,
                metodo.upper(),
                status_code,
                ip_origem,
                detalhe,
            ),
        )
        conexao.commit()


def listar_logs_operacoes(limite: int = 100) -> list[dict[str, Any]]:
    inicializar_tabelas_registro()
    limite_seguro = max(1, min(limite, 500))
    with _conectar() as conexao:
        registros = conexao.execute(
            """
            SELECT id, data_hora, metodo, rota, query_params, status_code, tempo_ms, ip_origem, user_agent, detalhe
            FROM logs_operacoes
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite_seguro,),
        ).fetchall()
    return [dict(registro) for registro in registros]


def listar_registros_auditoria(limite: int = 100, ator_id: Optional[str] = None) -> list[dict[str, Any]]:
    inicializar_tabelas_registro()
    limite_seguro = max(1, min(limite, 500))
    with _conectar() as conexao:
        if ator_id:
            registros = conexao.execute(
                """
                SELECT id, data_hora, ator_id, ator_nome, acao, recurso, metodo, status_code, ip_origem, detalhe
                FROM registros_auditoria
                WHERE ator_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (ator_id, limite_seguro),
            ).fetchall()
        else:
            registros = conexao.execute(
                """
                SELECT id, data_hora, ator_id, ator_nome, acao, recurso, metodo, status_code, ip_origem, detalhe
                FROM registros_auditoria
                ORDER BY id DESC
                LIMIT ?
                """,
                (limite_seguro,),
            ).fetchall()
    return [dict(registro) for registro in registros]
