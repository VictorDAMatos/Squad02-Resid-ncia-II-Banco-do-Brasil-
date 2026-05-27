from datetime import datetime
from pathlib import Path
from typing import Optional
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(DB_PATH, timeout=10)
    conexao.row_factory = sqlite3.Row
    return conexao


def linha_para_dict(row: Optional[sqlite3.Row]) -> dict:
    return dict(row) if row else {}


def tabela_existe(conexao: sqlite3.Connection, nome: str) -> bool:
    row = conexao.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (nome,),
    ).fetchone()
    return row is not None


def colunas_tabela(conexao: sqlite3.Connection, tabela: str) -> set[str]:
    try:
        rows = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
    except sqlite3.OperationalError:
        return set()
    return {row[1] for row in rows}


def garantir_coluna(conexao: sqlite3.Connection, tabela: str, coluna: str, tipo: str) -> None:
    if coluna not in colunas_tabela(conexao, tabela):
        conexao.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")


def inicializar_tabelas_fraude(conexao: Optional[sqlite3.Connection] = None) -> None:
    fechar = False
    if conexao is None:
        conexao = conectar()
        fechar = True

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conta TEXT NOT NULL,
            cidade TEXT NOT NULL,
            tipo_transacao TEXT NOT NULL,
            dispositivo TEXT NOT NULL
        )
        """
    )

    garantir_coluna(conexao, "transactions", "classificacao_risco", "TEXT")
    garantir_coluna(conexao, "transactions", "motivo_risco", "TEXT")
    garantir_coluna(conexao, "transactions", "pontos_risco", "INTEGER")
    garantir_coluna(conexao, "transactions", "status_transacao", "TEXT")
    garantir_coluna(conexao, "transactions", "status_conta", "TEXT")
    garantir_coluna(conexao, "transactions", "processado_em", "TEXT")

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
    if fechar:
        conexao.close()


def calcular_risco(transacao: dict) -> dict:
    valor = float(transacao.get("valor") or 0)
    hora = str(transacao.get("hora") or "00:00")[:5]
    dispositivo = str(transacao.get("dispositivo") or "").lower()
    tipo = str(transacao.get("tipo_transacao") or "").lower()

    if tipo == "deposito":
        return {
            "classificacao": "verde",
            "nivel": "Baixo",
            "classe": "baixo",
            "pontos": 0,
            "motivos": ["depósito registrado sem bloqueio automático"],
            "motivo": "depósito registrado sem bloqueio automático",
        }

    pontos = 0
    motivos = []

    if valor > 10000:
        pontos += 60
        motivos.append("valor crítico acima de R$ 10.000")
    elif valor > 5000:
        pontos += 35
        motivos.append("valor alto acima de R$ 5.000")
    elif valor > 3000:
        pontos += 20
        motivos.append("valor acima do padrão")

    if "00:00" <= hora <= "05:59":
        pontos += 55
        motivos.append("transação em horário crítico de madrugada")
    elif hora >= "23:00" or hora <= "06:59":
        pontos += 20
        motivos.append("transação em horário incomum")

    if dispositivo == "caixa_eletronico" and valor >= 5000:
        pontos += 35
        motivos.append("saque elevado em caixa eletrônico")
    elif dispositivo and dispositivo not in {"app_mobile", "web", "internet_banking", "caixa_eletronico", "frontend_usuario", "pix_frontend_usuario"}:
        pontos += 10
        motivos.append("dispositivo fora do padrão")

    if tipo == "pix" and valor > 7000:
        pontos += 20
        motivos.append("pix de alto valor")

    if pontos >= 70:
        classificacao = "vermelho"
        nivel = "Alto"
        classe = "alto"
    elif pontos >= 35:
        classificacao = "amarelo"
        nivel = "Médio"
        classe = "medio"
    else:
        classificacao = "verde"
        nivel = "Baixo"
        classe = "baixo"

    return {
        "classificacao": classificacao,
        "nivel": nivel,
        "classe": classe,
        "pontos": pontos,
        "motivos": motivos or ["transação dentro dos parâmetros normais"],
        "motivo": "; ".join(motivos or ["transação dentro dos parâmetros normais"]),
    }


def status_por_risco(classificacao: str) -> str:
    if classificacao == "vermelho":
        return "pendente"
    if classificacao == "amarelo":
        return "em análise"
    return "aprovada"


def registrar_justificativa(
    conexao: sqlite3.Connection,
    acao: str,
    justificativa: str,
    analista: str = "Sistema",
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


def conta_esta_bloqueada(conexao: sqlite3.Connection, conta: str) -> bool:
    inicializar_tabelas_fraude(conexao)
    row = conexao.execute(
        "SELECT id FROM contas_bloqueadas WHERE conta = ? AND status = 'Bloqueada'",
        (conta,),
    ).fetchone()
    if row:
        return True

    row = conexao.execute(
        """
        SELECT id FROM transactions
        WHERE conta = ? AND status_conta = 'Bloqueada'
        LIMIT 1
        """,
        (conta,),
    ).fetchone()
    return row is not None


def buscar_transacao(conexao: sqlite3.Connection, transacao_id: int) -> Optional[dict]:
    inicializar_tabelas_fraude(conexao)
    row = conexao.execute("SELECT * FROM transactions WHERE id = ?", (transacao_id,)).fetchone()
    return linha_para_dict(row) if row else None


def abrir_caso_analise(conexao: sqlite3.Connection, transacao: dict, risco: dict, status: str = "Pendente") -> None:
    if risco["classificacao"] == "verde":
        return

    conexao.execute(
        """
        INSERT OR IGNORE INTO analise_casos
            (transacao_id, conta, status, risco_nivel, risco_pontos, aberto_em, detalhe)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transacao["id"],
            transacao.get("conta"),
            status,
            risco["nivel"],
            risco["pontos"],
            agora(),
            risco["motivo"],
        ),
    )


def marcar_conta_bloqueada(
    conexao: sqlite3.Connection,
    conta: str,
    motivo: str,
    transacao_id: Optional[int] = None,
    analista: str = "Sistema automático",
) -> None:
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
        (conta, conta, motivo, transacao_id, agora(), analista),
    )
    conexao.execute("UPDATE transactions SET status_conta = 'Bloqueada' WHERE conta = ?", (conta,))


def atualizar_status_conta(conexao: sqlite3.Connection, conta: str, transacao_id: Optional[int] = None) -> dict:
    rows = conexao.execute(
        """
        SELECT classificacao_risco, COUNT(*) AS qtd
        FROM transactions
        WHERE conta = ?
        GROUP BY classificacao_risco
        """,
        (conta,),
    ).fetchall()

    contagem = {"verde": 0, "amarelo": 0, "vermelho": 0}
    for row in rows:
        cor = row["classificacao_risco"]
        if cor in contagem:
            contagem[cor] = row["qtd"]

    bloqueio_existente = conexao.execute(
        "SELECT id FROM contas_bloqueadas WHERE conta = ? AND status = 'Bloqueada'",
        (conta,),
    ).fetchone()

    motivo = None
    if contagem["vermelho"] > 0:
        motivo = "Bloqueio automático: conta possui transação de risco vermelho."
    elif contagem["amarelo"] >= 3:
        motivo = "Bloqueio automático: conta possui três ou mais transações de risco amarelo."

    if motivo:
        bloqueio_novo = bloqueio_existente is None
        marcar_conta_bloqueada(conexao, conta, motivo, transacao_id, "Sistema automático")
        return {"status_conta": "Bloqueada", "bloqueio_automatico": bloqueio_novo, "motivo_bloqueio": motivo, **contagem}

    if not bloqueio_existente:
        conexao.execute("UPDATE transactions SET status_conta = 'Ativa' WHERE conta = ?", (conta,))
        return {"status_conta": "Ativa", "bloqueio_automatico": False, "motivo_bloqueio": None, **contagem}

    conexao.execute("UPDATE transactions SET status_conta = 'Bloqueada' WHERE conta = ?", (conta,))
    return {"status_conta": "Bloqueada", "bloqueio_automatico": False, "motivo_bloqueio": "Conta já estava bloqueada.", **contagem}


def processar_transacao(conexao: sqlite3.Connection, transacao_id: int) -> dict:
    inicializar_tabelas_fraude(conexao)
    transacao = buscar_transacao(conexao, transacao_id)
    if not transacao:
        raise ValueError("Transação não encontrada")

    risco = calcular_risco(transacao)
    status_transacao = status_por_risco(risco["classificacao"])

    conexao.execute(
        """
        UPDATE transactions
        SET classificacao_risco = ?, motivo_risco = ?, pontos_risco = ?,
            status_transacao = ?, processado_em = ?
        WHERE id = ?
        """,
        (
            risco["classificacao"],
            risco["motivo"],
            risco["pontos"],
            status_transacao,
            agora(),
            transacao_id,
        ),
    )

    transacao["classificacao_risco"] = risco["classificacao"]
    transacao["motivo_risco"] = risco["motivo"]
    transacao["pontos_risco"] = risco["pontos"]
    transacao["status_transacao"] = status_transacao

    abrir_caso_analise(conexao, transacao, risco)
    status_conta = atualizar_status_conta(conexao, str(transacao.get("conta")), transacao_id)

    if status_conta["bloqueio_automatico"]:
        registrar_justificativa(
            conexao,
            "Bloqueio automático",
            status_conta["motivo_bloqueio"],
            "Sistema automático",
            transacao_id,
            str(transacao.get("conta")),
        )
        registrar_notificacao(
            conexao,
            "Bloqueio automático",
            f"Conta {transacao.get('conta')} bloqueada automaticamente após análise da transação {transacao_id}.",
            transacao_id,
            str(transacao.get("conta")),
        )

    return {
        "transacao_id": transacao_id,
        "conta": transacao.get("conta"),
        "risco": risco,
        "status_transacao": status_transacao,
        **status_conta,
    }


def processar_todas_transacoes(conexao: sqlite3.Connection) -> list[dict]:
    inicializar_tabelas_fraude(conexao)
    rows = conexao.execute("SELECT id FROM transactions ORDER BY id").fetchall()
    resultados = []
    for row in rows:
        resultados.append(processar_transacao(conexao, row["id"]))
    conexao.commit()
    return resultados


def desbloquear_conta_manual(conexao: sqlite3.Connection, conta: str, justificativa: str, analista: str) -> None:
    inicializar_tabelas_fraude(conexao)
    conexao.execute(
        "UPDATE contas_bloqueadas SET status = 'Desbloqueada' WHERE conta = ? AND status = 'Bloqueada'",
        (conta,),
    )
    conexao.execute("UPDATE transactions SET status_conta = 'Ativa' WHERE conta = ?", (conta,))
    registrar_justificativa(conexao, "Desbloqueio de conta", justificativa, analista, None, conta)
    registrar_notificacao(conexao, "Desbloqueio", f"Conta {conta} desbloqueada manualmente.", None, conta)


def atualizar_caso_manual(
    conexao: sqlite3.Connection,
    transacao_id: int,
    status: str,
    resultado: str,
    analista: str,
    detalhe: str,
) -> None:
    transacao = buscar_transacao(conexao, transacao_id)
    if not transacao:
        raise ValueError("Transação não encontrada")
    risco = calcular_risco(transacao)
    abrir_caso_analise(conexao, transacao, risco, status)
    conexao.execute(
        """
        UPDATE analise_casos
        SET status = ?, resultado = ?, risco_nivel = ?, risco_pontos = ?,
            atualizado_em = ?, analista = ?, detalhe = ?
        WHERE transacao_id = ?
        """,
        (status, resultado, risco["nivel"], risco["pontos"], agora(), analista, detalhe, transacao_id),
    )


def enriquecer_transacao(conexao: sqlite3.Connection, transacao: dict) -> dict:
    inicializar_tabelas_fraude(conexao)
    item = dict(transacao)
    risco = calcular_risco(item)
    item["risco"] = risco
    item["classificacao_risco"] = item.get("classificacao_risco") or risco["classificacao"]
    item["status_transacao"] = item.get("status_transacao") or status_por_risco(risco["classificacao"])
    item["status_conta"] = item.get("status_conta") or ("Bloqueada" if conta_esta_bloqueada(conexao, str(item.get("conta"))) else "Ativa")
    row = conexao.execute(
        "SELECT status FROM analise_casos WHERE transacao_id = ?",
        (item.get("id"),),
    ).fetchone()
    item["status_analise"] = row["status"] if row else item["status_transacao"]
    item["conta_bloqueada"] = item["status_conta"] == "Bloqueada"
    return item
