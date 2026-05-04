import sqlite3
import random
import requests
import time

URL_API = "http://127.0.0.1:8000/transactions"


def preparar_core_bancario_para_testes():
    """Garante que existem contas e cartões válidos na base de dados para o simulador usar."""
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    # Verifica se já tem contas cadastradas
    cursor.execute("SELECT numero FROM Conta")
    contas_db = cursor.fetchall()

    contas_validas = []
    cartoes_validos = {}  # Mapeia qual é o cartão de cada conta

    if not contas_db:
        print("⚙️ A preparar o Core Bancário com dados de teste...")

        # Cria 1 Agência Padrão
        cursor.execute("INSERT INTO Agencia (nome, numero, endereco) VALUES ('Sede', '0001', 'Avenida Central')")
        agencia_id = cursor.lastrowid

        # Cria 50 Clientes, Contas e Cartões em lote
        for i in range(1, 51):
            # Cliente
            cursor.execute("INSERT INTO Cliente_Core (nome, cpf) VALUES (?, ?)",
                           (f"Cliente Teste {i}", f"111222333{i:02d}"))
            cliente_id = cursor.lastrowid

            # Conta
            numero_conta = f"100{i}-X"
            cursor.execute("INSERT INTO Conta (numero, saldo, cliente_id, agencia_id) VALUES (?, 5000, ?, ?)",
                           (numero_conta, cliente_id, agencia_id))
            conta_id = cursor.lastrowid
            contas_validas.append(numero_conta)

            # Cartão
            numero_cartao = f"5555-4444-3333-22{i:02d}"
            cursor.execute("INSERT INTO Cartao (numero, validade, cvv, conta_id) VALUES (?, '12/30', '123', ?)",
                           (numero_cartao, conta_id))
            cartoes_validos[numero_conta] = numero_cartao

        conexao.commit()
        print("✅ 50 Contas e Cartões gerados com sucesso!")
    else:
        # Se já existirem dados, apenas os carrega para a memória do script
        for c in contas_db:
            contas_validas.append(c[0])

        cursor.execute("SELECT c.numero, ca.numero FROM Conta c JOIN Cartao ca ON c.id = ca.conta_id")
        for linha in cursor.fetchall():
            cartoes_validos[linha[0]] = linha[1]

    conexao.close()
    return contas_validas, cartoes_validos


def iniciar_simulador():
    # Prepara os dados válidos
    contas, cartoes = preparar_core_bancario_para_testes()

    print("🚀 A iniciar o envio de transações...")

    # Loop do simulador
    while True:
        # Escolhe uma conta real que existe na base de dados
        conta_escolhida = random.choice(contas)
        tipo = random.choice(["pix", "cartao_credito", "cartao_debito", "transferencia"])

        # Se for cartão, TEM de usar o cartão associado a esta conta
        if tipo in ["cartao_credito", "cartao_debito"]:
            dispositivo = cartoes.get(conta_escolhida, "app_mobile")
        else:
            dispositivo = random.choice(["app_mobile", "caixa_eletronico", "internet_banking"])

        dados_transacao = {
            "valor": round(random.uniform(10.0, 15000.0), 2),
            "data": "2023-10-25",
            "hora": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}",
            "categoria": random.choice(["alimentacao", "eletronicos", "servicos", "lazer"]),
            "conta": conta_escolhida,  # Usa uma conta válida!
            "cidade": random.choice(["Lisboa", "Porto", "Coimbra", "Faro"]),
            "tipo_transacao": tipo,
            "dispositivo": dispositivo  # Usa um cartão válido!
        }

        try:
            resposta = requests.post(URL_API, json=dados_transacao)
            print(
                f"[{resposta.status_code}] Transação enviada: {conta_escolhida} | {tipo} | €{dados_transacao['valor']}")
        except requests.exceptions.ConnectionError:
            print("❌ Erro: A API não está a correr. Inicie o main.py primeiro.")
            break

        time.sleep(2)  # Espera 2 segundos antes de enviar a próxima


if __name__ == "__main__":
    iniciar_simulador()