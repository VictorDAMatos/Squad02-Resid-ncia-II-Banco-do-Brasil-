"""Acesso ao banco de dados para a área do analista.

Repository = camada que conversa diretamente com o banco.
A rota não deve montar SQL; ela apenas chama o service.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"


class AnalistaRepository:
    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)

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

    def listar_colunas(self, tabela: str = "transactions") -> set[str]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({tabela})")
            return {linha[1] for linha in cursor.fetchall()}

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
        limite_sql = " LIMIT ?" if limite else ""
        parametros: list[Any] = [limite] if limite else []

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    {coluna} AS nome,
                    COUNT(*) AS qtd,
                    COALESCE(SUM(valor), 0) AS volume
                FROM transactions
                GROUP BY {coluna}
                ORDER BY volume DESC
                {limite_sql}
                """,
                parametros,
            )
            return self._rows_para_dict(cursor.fetchall())

    def agrupar_quantidade(self, coluna: str) -> list[dict[str, Any]]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {coluna} AS nome, COUNT(*) AS qtd
                FROM transactions
                GROUP BY {coluna}
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
                    SUBSTR(hora, 1, 2) AS hora_dia,
                    COUNT(*) AS qtd,
                    COALESCE(SUM(valor), 0) AS volume
                FROM transactions
                GROUP BY hora_dia
                ORDER BY hora_dia
                """
            )
            return self._rows_para_dict(cursor.fetchall())

    def ultimas_transacoes(self, limite: int = 10) -> list[dict[str, Any]]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transactions ORDER BY id DESC LIMIT ?",
                (limite,),
            )
            return self._rows_para_dict(cursor.fetchall())

    def listar_anomalias_detalhadas(self, limite: int = 50) -> list[dict[str, Any]]:
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    *,
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

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM transactions {where_sql}",
                parametros,
            )
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
            transacoes = self._rows_para_dict(cursor.fetchall())
            return total, transacoes

    def listar_contas_bloqueadas(self) -> list[dict[str, Any]]:
        colunas = self.listar_colunas()
        if "status_conta" not in colunas:
            return []

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM transactions
                WHERE LOWER(status_conta) IN ('bloqueada', 'suspensa', 'bloqueado', 'suspenso')
                ORDER BY id DESC
                """
            )
            return self._rows_para_dict(cursor.fetchall())

    def desbloquear_conta(self, conta_id: int) -> int:
        """Ativa uma conta bloqueada.

        Mantive compatibilidade com a versão antiga:
        - se existir coluna conta_id, atualiza por conta_id;
        - senão, tenta atualizar pelo id da transação.
        """
        colunas = self.listar_colunas()
        if "status_conta" not in colunas:
            return 0

        coluna_identificacao = "conta_id" if "conta_id" in colunas else "id"

        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE transactions SET status_conta = 'Ativa' WHERE {coluna_identificacao} = ?",
                (conta_id,),
            )
            conn.commit()
            return cursor.rowcount
