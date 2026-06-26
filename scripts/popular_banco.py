from pathlib import Path
import sqlite3
import random
from datetime import datetime, timedelta

from app.services.fraude_service import inicializar_tabelas_fraude

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "banco_brasil_transacoes.sqlite"


def preparar_core_bancario(cursor: sqlite3.Cursor) -> tuple[list[str], dict[str, str]]:
    """Garante tabelas e dados mínimos para gerar histórico de transações."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Agencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            numero TEXT,
            endereco TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Cliente_Core (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Conta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE,
            saldo REAL,
            cliente_id INTEGER,
            agencia_id INTEGER
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Cartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE,
            validade TEXT,
            cvv TEXT,
            limite REAL DEFAULT 0,
            tipo TEXT DEFAULT 'credito',
            conta_id TEXT
        )
        """
    )

    contas_db = cursor.execute("SELECT numero FROM Conta").fetchall()
    contas_validas: list[str] = []
    cartoes_validos: dict[str, str] = {}

    if not contas_db:
        print("⚙️ Criando Core Bancário para histórico massivo...")
        cursor.execute(
            "INSERT INTO Agencia (nome, numero, endereco) VALUES ('Sede Histórica', '0001', 'Avenida Central')"
        )
        agencia_id = cursor.lastrowid

        for i in range(1, 101):
            cursor.execute(
                "INSERT INTO Cliente_Core (nome, cpf) VALUES (?, ?)",
                (f"Cliente Histórico {i}", f"999888777{i:03d}"),
            )
            cliente_id = cursor.lastrowid

            numero_conta = f"500{i}-X"
            cursor.execute(
                "INSERT INTO Conta (numero, saldo, cliente_id, agencia_id) VALUES (?, 15000, ?, ?)",
                (numero_conta, cliente_id, agencia_id),
            )
            contas_validas.append(numero_conta)

            numero_cartao = f"4444-3333-2222-1{i:03d}"
            cursor.execute(
                "INSERT INTO Cartao (numero, validade, cvv, limite, tipo, conta_id) VALUES (?, '12/30', '123', 5000, 'credito', ?)",
                (numero_cartao, numero_conta),
            )
            cartoes_validos[numero_conta] = numero_cartao
    else:
        contas_validas = [linha[0] for linha in contas_db]
        for conta, cartao in cursor.execute("SELECT conta_id, numero FROM Cartao WHERE conta_id IS NOT NULL").fetchall():
            cartoes_validos[str(conta)] = str(cartao)

    return contas_validas, cartoes_validos


def popular_banco_massivo(total: int = 30000):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()

    inicializar_tabelas_fraude(conexao)
    contas_validas, cartoes_validos = preparar_core_bancario(cursor)
    conexao.commit()

    print("🧹 Limpando histórico antigo para evitar duplicações...")
    cursor.execute("DELETE FROM transactions")
    conexao.commit()

    print(f"🚀 Gerando {total:,} transações históricas...")
    transacoes_lote = []
    data_base = datetime.now()

    for _ in range(total):
        conta_escolhida = random.choice(contas_validas)
        tipo = random.choice(["pix", "cartao_credito", "cartao_debito", "transferencia"])

        if tipo in ["cartao_credito", "cartao_debito"]:
            dispositivo = cartoes_validos.get(conta_escolhida, "app_mobile")
        else:
            dispositivo = random.choice(["app_mobile", "caixa_eletronico", "internet_banking"])

        if random.random() < 0.05:
            valor = round(random.uniform(10500.0, 50000.0), 2)
            hora = f"{random.randint(0, 4):02d}:{random.randint(0, 59):02d}"
        else:
            valor = round(random.uniform(10.0, 2000.0), 2)
            hora = f"{random.randint(6, 23):02d}:{random.randint(0, 59):02d}"

        dias_atras = random.randint(0, 365)
        data_transacao = (data_base - timedelta(days=dias_atras)).strftime("%Y-%m-%d")

        transacoes_lote.append(
            (
                valor,
                data_transacao,
                hora,
                random.choice(["alimentacao", "eletronicos", "servicos", "lazer"]),
                conta_escolhida,
                random.choice(["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba"]),
                tipo,
                dispositivo,
            )
        )

    print("💾 Salvando no banco de dados...")
    cursor.executemany(
        """
        INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        transacoes_lote,
    )

    conexao.commit()
    conexao.close()
    print(f"✅ Sucesso! Tabela limpa e {total:,} transações foram inseridas.")


if __name__ == "__main__":
    popular_banco_massivo()
