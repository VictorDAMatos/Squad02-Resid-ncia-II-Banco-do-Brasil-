
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator

router = APIRouter(prefix="/usuario", tags=["📱 Portal do Usuário"])

BASE_DIR = Path(__file__).resolve().parents[3]
DB_TX   = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"
DB_AI   = BASE_DIR / "data" / "banco_brasil_ai.sqlite"

CONTA_PADRAO = "58392-1"
AGENCIA_PADRAO = "0042-3"
SALDO_INICIAL = 783.70
LIMITE_CREDITO = 3000.00

LIMITE_TRANSFERENCIA = 5000.00



def _conectar_tx() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_TX, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _agora() -> tuple[str, str]:
    """Retorna (data 'YYYY-MM-DD', hora 'HH:MM:SS') no fuso local."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


def _saldo_calculado() -> float:
    """
    Calcula o saldo a partir do saldo inicial + créditos − débitos
    registrados na tabela transactions para a conta padrão.

    Tipos do banco:
      Débitos  → 'transferencia', 'pix', 'cartao_credito', 'cartao_debito', 'sent'
      Créditos → 'deposit', 'received'
    """
    with _conectar_tx() as conn:
        row_deb = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS total
            FROM transactions
            WHERE conta = ?
              AND tipo_transacao IN ('transferencia', 'pix', 'cartao_credito', 'cartao_debito', 'sent')
            """,
            (CONTA_PADRAO,),
        ).fetchone()

        row_cred = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS total
            FROM transactions
            WHERE conta = ?
              AND tipo_transacao IN ('deposit', 'received')
            """,
            (CONTA_PADRAO,),
        ).fetchone()

        # A injeção de saldo do analista é registrada em saldo_injecoes.
        # Antes, o endpoint /usuario/saldo ignorava essa tabela e por isso
        # o POST /analista/injetar-saldo retornava 200 OK, mas o saldo visual
        # continuava igual. Somamos essas injeções como créditos de teste.
        tabela_injecoes = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'saldo_injecoes'
            """
        ).fetchone()

        if tabela_injecoes:
            row_inj = conn.execute(
                """
                SELECT COALESCE(SUM(valor), 0) AS total
                FROM saldo_injecoes
                WHERE conta = ?
                """,
                (CONTA_PADRAO,),
            ).fetchone()
        else:
            row_inj = None

    debitos  = row_deb["total"]  if row_deb  else 0.0
    creditos = row_cred["total"] if row_cred else 0.0
    injecoes = row_inj["total"]  if row_inj  else 0.0
    return round(SALDO_INICIAL + creditos + injecoes - debitos, 2)


def _gerar_protocolo() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")[:14]
    return f"BB{ts}"



class TransferenciaIn(BaseModel):
    nome_favorecido:   str
    conta_favorecido:  str
    valor:             float
    descricao:         Optional[str] = None

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return v


class PixIn(BaseModel):
    chave_pix: str
    valor:     float
    descricao: Optional[str] = None

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return v


class DepositoIn(BaseModel):
    valor: float

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return v



@router.get("/perfil")
def obter_perfil():
    """
    Retorna os dados de identificação do usuário logado.
    Espelha o objeto `state.user` do app.js.
    """
    return {
        "nome":    "Julia Andrade",
        "conta":   CONTA_PADRAO,
        "agencia": AGENCIA_PADRAO,
    }


@router.get("/saldo")
def obter_saldo():
    """
    Retorna o saldo atual e as informações de limite de crédito.
    Usado pelo `renderBalance()` e `updateBalanceBar()` do app.js.
    """
    saldo = _saldo_calculado()
    limite_disponivel = max(0.0, LIMITE_CREDITO - saldo)
    pct_utilizado     = round(min(100.0, ((LIMITE_CREDITO - saldo) / LIMITE_CREDITO) * 100), 1)

    return {
        "saldo":              saldo,
        "limite_credito":     LIMITE_CREDITO,
        "limite_disponivel":  limite_disponivel,
        "percentual_usado":   pct_utilizado,
        "alerta_critico":     pct_utilizado > 85,
    }


@router.get("/transacoes")
def listar_transacoes(
    tipo: Optional[str] = Query(
        default=None,
        description="Filtra por tipo: 'sent', 'received', 'deposit', 'pix'. Omitir = todos.",
    ),
    limite: int = Query(default=50, ge=1, le=200),
):
    """
    Retorna o histórico de transações da conta.
    Usado pelos filtros 'all / sent / received / deposit' do app.js.
    """
    with _conectar_tx() as conn:
        base_query = """
            SELECT id, valor, data, hora, categoria AS descricao,
                   tipo_transacao AS tipo, dispositivo AS nome,
                   cidade
            FROM transactions
            WHERE conta = ?
        """
        params: list = [CONTA_PADRAO]

        if tipo:
            base_query += " AND tipo_transacao = ?"
            params.append(tipo)

        base_query += " ORDER BY data DESC, hora DESC LIMIT ?"
        params.append(limite)

        rows = conn.execute(base_query, params).fetchall()

    transacoes = []
    for row in rows:
        d = dict(row)
        try:
            d["data_hora"] = f"{d['data']}T{d['hora']}"
        except Exception:
            d["data_hora"] = d.get("data", "")
        transacoes.append(d)

    return {"total": len(transacoes), "transacoes": transacoes}


@router.post("/transferencia", status_code=201)
def realizar_transferencia(body: TransferenciaIn):
    """
    Debita a conta do usuário e registra a transação como 'sent'.
    Validações:
      - saldo suficiente
      - valor não excede R$ 5.000 (limite sem autenticação adicional)
      - não transferir para a própria conta
    """
    conta_destino = body.conta_favorecido.strip()
    conta_propria = f"{AGENCIA_PADRAO} · {CONTA_PADRAO}"
    if conta_destino == conta_propria or conta_destino == CONTA_PADRAO:
        raise HTTPException(
            status_code=400,
            detail="Não é possível transferir para a própria conta.",
        )

    if body.valor > LIMITE_TRANSFERENCIA:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Transferências acima de R$ {LIMITE_TRANSFERENCIA:,.2f} "
                "requerem autenticação adicional no aplicativo BB."
            ),
        )

    saldo_atual = _saldo_calculado()
    if body.valor > saldo_atual:
        raise HTTPException(
            status_code=422,
            detail=f"Saldo insuficiente. Saldo disponível: R$ {saldo_atual:,.2f}.",
        )

    data_tx, hora_tx = _agora()
    protocolo = _gerar_protocolo()

    with _conectar_tx() as conn:
        conn.execute(
            """
            INSERT INTO transactions
                (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.valor,
                data_tx,
                hora_tx,
                body.descricao or "Transferência",
                CONTA_PADRAO,
                "Internet Banking",
                "sent",
                body.nome_favorecido,
            ),
        )
        conn.commit()

    saldo_novo = round(saldo_atual - body.valor, 2)

    return {
        "sucesso":          True,
        "protocolo":        protocolo,
        "favorecido":       body.nome_favorecido,
        "conta_favorecido": conta_destino,
        "valor":            body.valor,
        "saldo_apos":       saldo_novo,
        "data_hora":        f"{data_tx}T{hora_tx}",
    }


@router.post("/pix", status_code=201)
def realizar_pix(body: PixIn):
    """
    Debita a conta e registra como 'pix'.
    Validações: chave não vazia, saldo suficiente.
    """
    if not body.chave_pix.strip():
        raise HTTPException(status_code=400, detail="Informe a chave Pix do destinatário.")

    saldo_atual = _saldo_calculado()
    if body.valor > saldo_atual:
        raise HTTPException(
            status_code=422,
            detail=f"Saldo insuficiente para este Pix. Saldo disponível: R$ {saldo_atual:,.2f}.",
        )

    data_tx, hora_tx = _agora()
    protocolo = _gerar_protocolo()

    with _conectar_tx() as conn:
        conn.execute(
            """
            INSERT INTO transactions
                (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.valor,
                data_tx,
                hora_tx,
                body.descricao or "Pix enviado",
                CONTA_PADRAO,
                "Pix",
                "pix",
                f"Pix → {body.chave_pix}",
            ),
        )
        conn.commit()

    return {
        "sucesso":    True,
        "protocolo":  protocolo,
        "chave_pix":  body.chave_pix,
        "valor":      body.valor,
        "saldo_apos": round(saldo_atual - body.valor, 2),
        "data_hora":  f"{data_tx}T{hora_tx}",
    }


@router.post("/deposito", status_code=201)
def realizar_deposito(body: DepositoIn):
    """
    Credita a conta e registra como 'deposit'.
    """
    saldo_atual = _saldo_calculado()
    data_tx, hora_tx = _agora()
    protocolo = _gerar_protocolo()

    with _conectar_tx() as conn:
        conn.execute(
            """
            INSERT INTO transactions
                (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.valor,
                data_tx,
                hora_tx,
                "Depósito",
                CONTA_PADRAO,
                "Internet Banking",
                "deposit",
                "Crédito em conta",
            ),
        )
        conn.commit()

    return {
        "sucesso":    True,
        "protocolo":  protocolo,
        "valor":      body.valor,
        "saldo_apos": round(saldo_atual + body.valor, 2),
        "data_hora":  f"{data_tx}T{hora_tx}",
    }


@router.get("/extrato/exportar", response_class=PlainTextResponse)
def exportar_extrato(
    tipo: Optional[str] = Query(
        default=None,
        description="Filtra por tipo: 'sent', 'received', 'deposit', 'pix'. Omitir = todos.",
    ),
):
    """
    Devolve o extrato em texto puro para download.
    Espelha a função `exportTransactions()` do app.js.
    """
    with _conectar_tx() as conn:
        base_query = """
            SELECT valor, data, hora, categoria, tipo_transacao, dispositivo
            FROM transactions
            WHERE conta = ?
        """
        params: list = [CONTA_PADRAO]

        if tipo:
            base_query += " AND tipo_transacao = ?"
            params.append(tipo)

        base_query += " ORDER BY data DESC, hora DESC"
        rows = conn.execute(base_query, params).fetchall()

    if not rows:
        return PlainTextResponse(
            content="Nenhuma movimentação encontrada.",
            media_type="text/plain; charset=utf-8",
        )

    linhas = [f"EXTRATO BB — Conta {CONTA_PADRAO} | Agência {AGENCIA_PADRAO}", ""]
    for i, row in enumerate(rows, start=1):
        sinal = "-" if row["tipo_transacao"] in ("sent", "pix") else "+"
        linhas.append(
            f"{i:>4}. {row['data']} {row['hora']} "
            f"| {row['dispositivo']:<30} "
            f"| {row['categoria']:<25} "
            f"| {sinal}R$ {row['valor']:>10.2f}"
        )

    return PlainTextResponse(
        content="\n".join(linhas),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="extrato-bb-{tipo or "all"}.txt"'
        },
    )


def _criar_tabelas_extras():
    with _conectar_tx() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS boletos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo       TEXT NOT NULL,
                beneficiario TEXT NOT NULL,
                valor        REAL NOT NULL,
                vencimento   TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pendente',
                conta        TEXT NOT NULL,
                criado_em    TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                valor         REAL NOT NULL,
                parcelas      INTEGER NOT NULL,
                taxa_mensal   REAL NOT NULL,
                valor_parcela REAL NOT NULL,
                total_pagar   REAL NOT NULL,
                status        TEXT NOT NULL DEFAULT 'simulado',
                conta         TEXT NOT NULL,
                criado_em     TEXT NOT NULL
            )
        """)
        conn.commit()

_criar_tabelas_extras()



class BoletoGerarIn(BaseModel):
    beneficiario: str
    valor: float
    vencimento: str

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return v


class BoletoPagarIn(BaseModel):
    codigo: str


class EmprestimoSimularIn(BaseModel):
    valor: float
    parcelas: int

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return v

    @field_validator("parcelas")
    @classmethod
    def parcelas_validas(cls, v):
        if v not in [6, 12, 24, 36, 48, 60]:
            raise ValueError("Parcelas disponíveis: 6, 12, 24, 36, 48 ou 60.")
        return v



@router.post("/boleto/gerar", status_code=201)
def gerar_boleto(body: BoletoGerarIn):
    import random, string
    codigo = (
        "".join(random.choices(string.digits, k=10)) + "." +
        "".join(random.choices(string.digits, k=5)) + " " +
        "".join(random.choices(string.digits, k=10)) + "." +
        "".join(random.choices(string.digits, k=6)) + " " +
        "".join(random.choices(string.digits, k=10)) + "." +
        "".join(random.choices(string.digits, k=6)) + " " +
        random.choice(string.digits) + " " +
        "".join(random.choices(string.digits, k=14))
    )
    data_tx, hora_tx = _agora()
    with _conectar_tx() as conn:
        conn.execute(
            "INSERT INTO boletos (codigo, beneficiario, valor, vencimento, status, conta, criado_em) VALUES (?,?,?,?,'pendente',?,?)",
            (codigo, body.beneficiario, body.valor, body.vencimento, CONTA_PADRAO, f"{data_tx}T{hora_tx}"),
        )
        conn.commit()
    return {"sucesso": True, "codigo": codigo, "beneficiario": body.beneficiario,
            "valor": body.valor, "vencimento": body.vencimento, "status": "pendente", "criado_em": f"{data_tx}T{hora_tx}"}


@router.post("/boleto/pagar", status_code=200)
def pagar_boleto(body: BoletoPagarIn):
    with _conectar_tx() as conn:
        boleto = conn.execute(
            "SELECT * FROM boletos WHERE codigo = ? AND conta = ?",
            (body.codigo.strip(), CONTA_PADRAO),
        ).fetchone()
        if not boleto:
            raise HTTPException(status_code=404, detail="Boleto não encontrado.")
        if boleto["status"] == "pago":
            raise HTTPException(status_code=400, detail="Este boleto já foi pago.")
        saldo_atual = _saldo_calculado()
        if boleto["valor"] > saldo_atual:
            raise HTTPException(status_code=422, detail=f"Saldo insuficiente. Disponível: R$ {saldo_atual:,.2f}.")
        data_tx, hora_tx = _agora()
        conn.execute(
            "INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo) VALUES (?,?,?,?,?,?,?,?)",
            (boleto["valor"], data_tx, hora_tx, "Pagamento de boleto", CONTA_PADRAO, "Internet Banking", "sent", boleto["beneficiario"]),
        )
        conn.execute("UPDATE boletos SET status = 'pago' WHERE codigo = ?", (body.codigo.strip(),))
        conn.commit()
    return {"sucesso": True, "beneficiario": boleto["beneficiario"],
            "valor": boleto["valor"], "saldo_apos": round(saldo_atual - boleto["valor"], 2), "data_hora": f"{data_tx}T{hora_tx}"}


@router.get("/boleto/listar")
def listar_boletos():
    with _conectar_tx() as conn:
        rows = conn.execute(
            "SELECT * FROM boletos WHERE conta = ? ORDER BY criado_em DESC", (CONTA_PADRAO,)
        ).fetchall()
    return {"boletos": [dict(r) for r in rows]}



TAXAS = {6: 1.99, 12: 2.29, 24: 2.59, 36: 2.89, 48: 3.19, 60: 3.49}


@router.post("/emprestimo/simular", status_code=201)
def simular_emprestimo(body: EmprestimoSimularIn):
    taxa = TAXAS[body.parcelas] / 100
    valor_parcela = round(
        body.valor * (taxa * (1 + taxa) ** body.parcelas) /
        ((1 + taxa) ** body.parcelas - 1), 2
    )
    total_pagar = round(valor_parcela * body.parcelas, 2)
    data_tx, hora_tx = _agora()
    with _conectar_tx() as conn:
        conn.execute(
            "INSERT INTO emprestimos (valor, parcelas, taxa_mensal, valor_parcela, total_pagar, status, conta, criado_em) VALUES (?,?,?,?,?,'simulado',?,?)",
            (body.valor, body.parcelas, TAXAS[body.parcelas], valor_parcela, total_pagar, CONTA_PADRAO, f"{data_tx}T{hora_tx}"),
        )
        conn.commit()
    return {
        "sucesso": True, "valor": body.valor, "parcelas": body.parcelas,
        "taxa_mensal": TAXAS[body.parcelas], "valor_parcela": valor_parcela,
        "total_pagar": total_pagar, "criado_em": f"{data_tx}T{hora_tx}",
        "tabela_parcelas": [{"parcela": i+1, "valor": valor_parcela} for i in range(min(body.parcelas, 6))],
    }


@router.get("/emprestimo/listar")
def listar_emprestimos():
    with _conectar_tx() as conn:
        rows = conn.execute(
            "SELECT * FROM emprestimos WHERE conta = ? ORDER BY criado_em DESC", (CONTA_PADRAO,)
        ).fetchall()
    return {"emprestimos": [dict(r) for r in rows]}
