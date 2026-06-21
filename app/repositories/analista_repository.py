"""Acesso ao banco de dados para a área do analista.

Repository = camada que conversa diretamente com o banco.
A rota não monta SQL; ela apenas chama o service.

Esta versão também prepara o banco automaticamente:
- cria a pasta data/ quando necessário;
- cria a tabela transactions se ela ainda não existir;
- adiciona colunas necessárias caso a tabela já exista;
- cria tabelas de apoio para auditoria, notificações, injeções de saldo e SLA.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"


class AnalistaRepository:
    """Centraliza toda conversa com o SQLite."""

    COLUNAS_TRANSACTIONS: dict[str, str] = {
        "cpf": "TEXT",
        "conta": "TEXT",
        "conta_id": "TEXT",
        "valor": "REAL DEFAULT 0",
        "hora": "TEXT",
        "categoria": "TEXT",
        "tipo_transacao": "TEXT",
        "cidade": "TEXT",
        "dispositivo": "TEXT",
        "status_transacao": "TEXT DEFAULT 'pendente'",
        "status": "TEXT DEFAULT 'pendente'",
        "status_conta": "TEXT DEFAULT 'Ativa'",
        "saldo": "REAL DEFAULT 0",
        "data_hora": "TEXT",
        "criado_em": "DATETIME",
    }

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.preparar_banco()

    @contextmanager
    def conectar(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _rows_para_dict(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]

    def tabela_existe(self, tabela: str) -> bool:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                (tabela,),
            )
            return cursor.fetchone() is not None

    def listar_colunas(self, tabela: str = "transactions") -> set[str]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({tabela})")
            return {linha[1] for linha in cursor.fetchall()}

    def _coluna_id(self) -> str:
        """Usa id quando existir; caso contrário, usa o rowid interno do SQLite."""
        return "id" if "id" in self.listar_colunas() else "rowid"

    def _select_transactions(self) -> str:
        """Garante que consultas sempre devolvam um campo id."""
        return "SELECT *" if "id" in self.listar_colunas() else "SELECT rowid AS id, *"

    def preparar_banco(self) -> None:
        """Cria/atualiza a estrutura necessária para todos os requisitos funcionarem."""
        with self.conectar() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpf TEXT,
                    conta TEXT,
                    conta_id TEXT,
                    valor REAL DEFAULT 0,
                    hora TEXT,
                    categoria TEXT,
                    tipo_transacao TEXT,
                    cidade TEXT,
                    dispositivo TEXT,
                    status_transacao TEXT DEFAULT 'pendente',
                    status TEXT DEFAULT 'pendente',
                    status_conta TEXT DEFAULT 'Ativa',
                    saldo REAL DEFAULT 0,
                    data_hora TEXT,
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute("PRAGMA table_info(transactions)")
            existentes = {linha[1] for linha in cursor.fetchall()}
            for coluna, definicao in self.COLUNAS_TRANSACTIONS.items():
                if coluna not in existentes:
                    try:
                        cursor.execute(f"ALTER TABLE transactions ADD COLUMN {coluna} {definicao}")
                    except sqlite3.OperationalError as exc:
                        # SQLite não permite adicionar coluna com DEFAULT não constante em tabela existente.
                        # Reexecuta sem o DEFAULT para manter compatibilidade com bancos já populados.
                        if "non-constant default" in str(exc).lower():
                            definicao_sem_default = definicao.split(" DEFAULT " )[0]
                            cursor.execute(f"ALTER TABLE transactions ADD COLUMN {coluna} {definicao_sem_default}")
                        else:
                            raise

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analista_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entidade TEXT NOT NULL,
                    entidade_id TEXT,
                    acao TEXT NOT NULL,
                    justificativa TEXT,
                    analista TEXT DEFAULT 'analista',
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suspeito TEXT NOT NULL,
                    transacao_id INTEGER,
                    mensagem TEXT NOT NULL,
                    canal TEXT DEFAULT 'sistema',
                    analista TEXT DEFAULT 'sistema',
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS saldo_injecoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conta TEXT NOT NULL,
                    valor REAL NOT NULL,
                    justificativa TEXT NOT NULL,
                    analista TEXT DEFAULT 'analista',
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS account_balances (
                    conta TEXT PRIMARY KEY,
                    saldo REAL DEFAULT 0,
                    ultimo_analista TEXT,
                    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analises_sla (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transacao_id INTEGER NOT NULL UNIQUE,
                    status TEXT DEFAULT 'em_analise',
                    risco TEXT,
                    iniciado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolvido_em DATETIME,
                    analista TEXT,
                    justificativa TEXT
                )
                """
            )

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_cpf ON transactions(cpf)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_conta ON transactions(conta)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_conta_id ON transactions(conta_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status_conta ON transactions(status_conta)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_suspeito ON notification_logs(suspeito)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_entidade_id ON analista_audit_logs(entidade_id)")
            conn.commit()

    # Mantido por compatibilidade com a versão anterior.
    def preparar_tabelas_apoio(self) -> None:
        self.preparar_banco()

    def buscar_kpis(self) -> dict[str, Any]:
        with self.conectar() as conn:
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
                WHERE valor > 5000 OR hora BETWEEN '00:00' AND '05:59'
                """
            )
            kpis["total_anomalias"] = cursor.fetchone()["total_anomalias"]
            return kpis

    def agrupar_com_volume(self, coluna: str, limite: int | None = None) -> list[dict[str, Any]]:
        if coluna not in self.listar_colunas():
            return []

        limite_sql = " LIMIT ?" if limite else ""
        parametros: list[Any] = [limite] if limite else []

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    COALESCE(NULLIF(CAST({coluna} AS TEXT), ''), 'Não informado') AS nome,
                    COUNT(*) AS qtd,
                    COALESCE(SUM(valor), 0) AS volume
                FROM transactions
                GROUP BY nome
                ORDER BY volume DESC
                {limite_sql}
                """,
                parametros,
            )
            return self._rows_para_dict(cursor.fetchall())

    def agrupar_quantidade(self, coluna: str) -> list[dict[str, Any]]:
        if coluna not in self.listar_colunas():
            return []

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT COALESCE(NULLIF(CAST({coluna} AS TEXT), ''), 'Não informado') AS nome, COUNT(*) AS qtd
                FROM transactions
                GROUP BY nome
                ORDER BY qtd DESC
                """
            )
            return self._rows_para_dict(cursor.fetchall())

    def agrupar_por_hora(self) -> list[dict[str, Any]]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COALESCE(NULLIF(SUBSTR(hora, 1, 2), ''), 'NI') AS hora_dia,
                    COUNT(*) AS qtd,
                    COALESCE(SUM(valor), 0) AS volume
                FROM transactions
                GROUP BY hora_dia
                ORDER BY hora_dia
                """
            )
            return self._rows_para_dict(cursor.fetchall())

    def ultimas_transacoes(self, limite: int = 10) -> list[dict[str, Any]]:
        id_col = self._coluna_id()
        select_sql = self._select_transactions()
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"{select_sql} FROM transactions ORDER BY {id_col} DESC LIMIT ?",
                (limite,),
            )
            return self._rows_para_dict(cursor.fetchall())

    def buscar_transacao_por_id(self, transacao_id: int) -> dict[str, Any] | None:
        id_col = self._coluna_id()
        select_sql = self._select_transactions()
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{select_sql} FROM transactions WHERE {id_col} = ?", (transacao_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_anomalias_detalhadas(self, limite: int = 50) -> list[dict[str, Any]]:
        select_sql = self._select_transactions()
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                {select_sql},
                    CASE
                        WHEN valor > 10000 THEN 'Valor Muito Alto (> R$10.000)'
                        WHEN hora BETWEEN '00:00' AND '05:59' THEN 'Horário Suspeito (Madrugada)'
                        WHEN dispositivo = 'caixa_eletronico' AND valor > 5000 THEN 'Saque Alto em Caixa Eletrônico'
                        ELSE 'Valor Alto (> R$5.000)'
                    END AS regra_alerta
                FROM transactions
                WHERE valor > 5000 OR hora BETWEEN '00:00' AND '05:59'
                ORDER BY valor DESC
                LIMIT ?
                """,
                (limite,),
            )
            return self._rows_para_dict(cursor.fetchall())

    def listar_categorias(self) -> list[str]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT categoria
                FROM transactions
                WHERE categoria IS NOT NULL AND categoria != ''
                ORDER BY categoria
                """
            )
            return [row["categoria"] for row in cursor.fetchall()]

    def filtrar_transacoes(
        self,
        filtros_sql: list[str],
        parametros: list[Any],
        limite: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        where_sql = f"WHERE {' AND '.join(filtros_sql)}" if filtros_sql else ""
        id_col = self._coluna_id()
        select_sql = self._select_transactions()

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) AS total FROM transactions {where_sql}", parametros)
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                {select_sql}
                FROM transactions
                {where_sql}
                ORDER BY {id_col} DESC
                LIMIT ?
                """,
                [*parametros, limite],
            )
            transacoes = self._rows_para_dict(cursor.fetchall())
            return total, transacoes

    def listar_transacoes_para_filtro_risco(self, limite: int = 500) -> list[dict[str, Any]]:
        id_col = self._coluna_id()
        select_sql = self._select_transactions()
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{select_sql} FROM transactions ORDER BY {id_col} DESC LIMIT ?", (limite,))
            return self._rows_para_dict(cursor.fetchall())

    def listar_contas_bloqueadas(self) -> list[dict[str, Any]]:
        id_col = self._coluna_id()
        select_sql = self._select_transactions()
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                {select_sql}
                FROM transactions
                WHERE LOWER(COALESCE(status_conta, '')) IN ('bloqueada', 'suspensa', 'bloqueado', 'suspenso')
                ORDER BY {id_col} DESC
                """
            )
            return self._rows_para_dict(cursor.fetchall())

    def desbloquear_conta(self, conta_id: str) -> int:
        """Ativa uma conta bloqueada por id, conta ou conta_id."""
        colunas = self.listar_colunas()
        filtros: list[str] = []
        parametros: list[Any] = []

        for coluna in ("conta", "conta_id"):
            if coluna in colunas:
                filtros.append(f"CAST({coluna} AS TEXT) = ?")
                parametros.append(str(conta_id))

        id_col = self._coluna_id()
        filtros.append(f"CAST({id_col} AS TEXT) = ?")
        parametros.append(str(conta_id))

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE transactions
                SET status_conta = 'Ativa'
                WHERE ({' OR '.join(filtros)})
                  AND LOWER(COALESCE(status_conta, '')) IN ('bloqueada', 'suspensa', 'bloqueado', 'suspenso')
                """,
                parametros,
            )
            conn.commit()
            return cursor.rowcount

    def atualizar_fluxo_transacao(self, transacao_id: int, status_transacao: str, status_conta: str | None = None) -> dict[str, Any]:
        id_col = self._coluna_id()
        campos: list[str] = ["status_transacao = ?", "status = ?"]
        parametros: list[Any] = [status_transacao, status_transacao]

        if status_conta:
            campos.append("status_conta = ?")
            parametros.append(status_conta)

        with self.conectar() as conn:
            cursor = conn.cursor()
            parametros.append(transacao_id)
            cursor.execute(f"UPDATE transactions SET {', '.join(campos)} WHERE {id_col} = ?", parametros)
            conn.commit()

        return self.buscar_transacao_por_id(transacao_id) or {}

    def registrar_auditoria(self, entidade: str, entidade_id: str | int, acao: str, justificativa: str, analista: str = "analista") -> int:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO analista_audit_logs (entidade, entidade_id, acao, justificativa, analista)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entidade, str(entidade_id), acao, justificativa, analista),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def registrar_notificacao(self, suspeito: str, mensagem: str, canal: str = "sistema", transacao_id: int | None = None, analista: str = "sistema") -> int:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO notification_logs (suspeito, transacao_id, mensagem, canal, analista)
                VALUES (?, ?, ?, ?, ?)
                """,
                (suspeito, transacao_id, mensagem, canal, analista),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def listar_notificacoes(self, suspeito: str | None = None, limite: int = 100) -> list[dict[str, Any]]:
        filtros = "WHERE suspeito = ?" if suspeito else ""
        parametros: list[Any] = [suspeito] if suspeito else []
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *
                FROM notification_logs
                {filtros}
                ORDER BY id DESC
                LIMIT ?
                """,
                [*parametros, limite],
            )
            return self._rows_para_dict(cursor.fetchall())

    def listar_auditoria_por_entidades(self, entidade_ids: list[str | int], limite: int = 100) -> list[dict[str, Any]]:
        ids = [str(item) for item in entidade_ids if item is not None]
        if not ids:
            return []

        placeholders = ",".join("?" for _ in ids)
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *
                FROM analista_audit_logs
                WHERE entidade_id IN ({placeholders})
                ORDER BY id DESC
                LIMIT ?
                """,
                [*ids, limite],
            )
            return self._rows_para_dict(cursor.fetchall())

    def listar_auditoria_por_entidade(self, entidade_id: str | int, limite: int = 100) -> list[dict[str, Any]]:
        return self.listar_auditoria_por_entidades([entidade_id], limite=limite)

    def listar_transacoes_do_suspeito(self, suspeito: str, limite: int = 100) -> list[dict[str, Any]]:
        colunas = self.listar_colunas()
        filtros: list[str] = []
        parametros: list[Any] = []

        for coluna in ("cpf", "conta", "conta_id"):
            if coluna in colunas:
                filtros.append(f"CAST({coluna} AS TEXT) = ?")
                parametros.append(suspeito)

        if not filtros:
            return []

        id_col = self._coluna_id()
        select_sql = self._select_transactions()
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                {select_sql}
                FROM transactions
                WHERE {' OR '.join(filtros)}
                ORDER BY {id_col} DESC
                LIMIT ?
                """,
                [*parametros, limite],
            )
            return self._rows_para_dict(cursor.fetchall())

    def listar_dispositivos_do_suspeito(self, suspeito: str) -> list[dict[str, Any]]:
        colunas = self.listar_colunas()
        if "dispositivo" not in colunas:
            return []

        filtros: list[str] = []
        parametros: list[Any] = []
        for coluna in ("cpf", "conta", "conta_id"):
            if coluna in colunas:
                filtros.append(f"CAST({coluna} AS TEXT) = ?")
                parametros.append(suspeito)

        if not filtros:
            return []

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT dispositivo, COUNT(*) AS qtd, COALESCE(SUM(valor), 0) AS volume
                FROM transactions
                WHERE {' OR '.join(filtros)}
                GROUP BY dispositivo
                ORDER BY qtd DESC
                """,
                parametros,
            )
            return self._rows_para_dict(cursor.fetchall())

    def buscar_historico_dispositivo(self, transacao: dict[str, Any]) -> dict[str, Any]:
        colunas = self.listar_colunas()
        if "dispositivo" not in colunas or "dispositivo" not in transacao:
            return {"disponivel": False, "mensagem": "A base não possui coluna de dispositivo."}

        filtros: list[str] = []
        parametros: list[Any] = []
        for coluna in ("cpf", "conta", "conta_id"):
            if coluna in colunas and transacao.get(coluna) is not None:
                filtros.append(f"CAST({coluna} AS TEXT) = ?")
                parametros.append(str(transacao[coluna]))

        if not filtros:
            return {"disponivel": False, "mensagem": "Não há CPF/conta para comparar o dispositivo."}

        id_col = self._coluna_id()
        transacao_id = transacao.get("id")
        dispositivo_atual = transacao.get("dispositivo")
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT dispositivo, COUNT(*) AS qtd
                FROM transactions
                WHERE ({' OR '.join(filtros)}) AND {id_col} != ?
                GROUP BY dispositivo
                ORDER BY qtd DESC
                """,
                [*parametros, transacao_id],
            )
            historico = self._rows_para_dict(cursor.fetchall())

        total_historico = sum(item["qtd"] for item in historico)
        ja_usado = any(item["dispositivo"] == dispositivo_atual for item in historico)
        mais_usado = historico[0]["dispositivo"] if historico else None
        return {
            "disponivel": True,
            "dispositivo_atual": dispositivo_atual,
            "dispositivo_ja_usado": ja_usado,
            "dispositivo_mais_usado": mais_usado,
            "total_transacoes_historicas": total_historico,
            "historico": historico,
        }

    def registrar_injecao_saldo(self, conta: str, valor: float, justificativa: str, analista: str) -> int:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO saldo_injecoes (conta, valor, justificativa, analista)
                VALUES (?, ?, ?, ?)
                """,
                (conta, valor, justificativa, analista),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def tentar_atualizar_saldo_conta(self, conta: str, valor: float, analista: str = "analista") -> int:
        """Atualiza saldo em uma tabela própria e também reflete em transactions quando possível."""
        linhas_atualizadas = 0
        colunas = self.listar_colunas()
        with self.conectar() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT conta FROM account_balances WHERE conta = ?", (conta,))
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE account_balances
                    SET saldo = COALESCE(saldo, 0) + ?, ultimo_analista = ?, atualizado_em = CURRENT_TIMESTAMP
                    WHERE conta = ?
                    """,
                    (valor, analista, conta),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO account_balances (conta, saldo, ultimo_analista)
                    VALUES (?, ?, ?)
                    """,
                    (conta, valor, analista),
                )
            linhas_atualizadas += max(cursor.rowcount, 0)

            filtros = []
            parametros: list[Any] = []
            for coluna in ("conta", "conta_id"):
                if coluna in colunas:
                    filtros.append(f"CAST({coluna} AS TEXT) = ?")
                    parametros.append(conta)

            if filtros:
                cursor.execute(
                    f"""
                    UPDATE transactions
                    SET saldo = COALESCE(saldo, 0) + ?
                    WHERE {' OR '.join(filtros)}
                    """,
                    [valor, *parametros],
                )
                linhas_atualizadas += max(cursor.rowcount, 0)

            conn.commit()
            return linhas_atualizadas

    def iniciar_analise_sla(self, transacao_id: int, risco: str) -> None:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE analises_sla
                SET status = 'em_analise', risco = ?, iniciado_em = CURRENT_TIMESTAMP,
                    resolvido_em = NULL, analista = NULL, justificativa = NULL
                WHERE transacao_id = ?
                """,
                (risco, transacao_id),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO analises_sla (transacao_id, risco)
                    VALUES (?, ?)
                    """,
                    (transacao_id, risco),
                )
            conn.commit()

    def resolver_analise_sla(self, transacao_id: int, status_final: str, justificativa: str, analista: str) -> int:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE analises_sla
                SET status = ?, resolvido_em = CURRENT_TIMESTAMP, justificativa = ?, analista = ?
                WHERE transacao_id = ? AND resolvido_em IS NULL
                """,
                (status_final, justificativa, analista, transacao_id),
            )
            conn.commit()
            return cursor.rowcount

    def buscar_sla_transacao(self, transacao_id: int) -> dict[str, Any] | None:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    *,
                    CAST((julianday(COALESCE(resolvido_em, CURRENT_TIMESTAMP)) - julianday(iniciado_em)) * 24 * 60 AS INTEGER) AS minutos_em_analise
                FROM analises_sla
                WHERE transacao_id = ?
                """,
                (transacao_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def listar_sla(self, somente_abertas: bool = False, limite: int = 100) -> list[dict[str, Any]]:
        where_sql = "WHERE resolvido_em IS NULL" if somente_abertas else ""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    *,
                    CAST((julianday(COALESCE(resolvido_em, CURRENT_TIMESTAMP)) - julianday(iniciado_em)) * 24 * 60 AS INTEGER) AS minutos_em_analise
                FROM analises_sla
                {where_sql}
                ORDER BY iniciado_em DESC
                LIMIT ?
                """,
                (limite,),
            )
            return self._rows_para_dict(cursor.fetchall())
