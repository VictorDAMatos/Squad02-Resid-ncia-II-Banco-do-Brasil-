import sqlite3
import random
from datetime import datetime, timedelta


def popular_banco_massivo():
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    # Evita duplicatas se rodar o script várias vezes

    print("🧹 Limpando histórico antigo para evitar duplicações...")
    cursor.execute("DELETE FROM transactions")
    conexao.commit()

    # PREPARAR CORE BANCÁRIO (Garante Contas Válidas)

    cursor.execute("SELECT numero FROM Conta")
    contas_db = cursor.fetchall()

    contas_validas = []
    cartoes_validos = {}

    if not contas_db:
        print("⚙️ A criar o Core Bancário para histórico massivo...")
        cursor.execute(
            "INSERT INTO Agencia (nome, numero, endereco) VALUES ('Sede Histórica', '0001', 'Avenida Central')")
        agencia_id = cursor.lastrowid

        for i in range(1, 101):
            cursor.execute("INSERT INTO Cliente_Core (nome, cpf) VALUES (?, ?)",
                           (f"Cliente Histórico {i}", f"999888777{i:03d}"))
            cliente_id = cursor.lastrowid

            numero_conta = f"500{i}-X"
            cursor.execute("INSERT INTO Conta (numero, saldo, cliente_id, agencia_id) VALUES (?, 15000, ?, ?)",
                           (numero_conta, cliente_id, agencia_id))
            conta_id = cursor.lastrowid
            contas_validas.append(numero_conta)

            numero_cartao = f"4444-3333-2222-1{i:03d}"
            cursor.execute("INSERT INTO Cartao (numero, validade, cvv, conta_id) VALUES (?, '12/30', '123', ?)",
                           (numero_cartao, conta_id))
            cartoes_validos[numero_conta] = numero_cartao

        conexao.commit()
    else:
        for c in contas_db:
            contas_validas.append(c[0])
        cursor.execute("SELECT c.numero, ca.numero FROM Conta c JOIN Cartao ca ON c.id = ca.conta_id")
        for linha in cursor.fetchall():
            cartoes_validos[linha[0]] = linha[1]

    # GERAR 30.000 TRANSAÇÕES VÁLIDAS E ÚNICAS

    print("🚀 A gerar 30.000 transações históricas...")
    transacoes_lote = []
    data_base = datetime.now()

    for _ in range(30000):
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

        categoria = random.choice(["alimentacao", "eletronicos", "servicos", "lazer"])
        cidade = random.choice(["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba"])

        transacoes_lote.append((valor, data_transacao, hora, categoria, conta_escolhida, cidade, tipo, dispositivo))

    # INSERÇÃO MASSIVA NO BANCO DE DADOS

    print("💾 A salvar no banco de dados...")

    cursor.executemany('''
        INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', transacoes_lote)

    conexao.commit()
    conexao.close()

    print("Sucesso! Tabela limpa e 30.000 transações fresquinhas foram inseridas.")


if __name__ == "__main__":
    popular_banco_massivo()