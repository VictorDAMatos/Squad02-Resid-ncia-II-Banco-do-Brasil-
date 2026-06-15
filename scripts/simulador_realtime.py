import sqlite3
import random
import requests
import time
from datetime import datetime

URL_API = "http://127.0.0.1:8000/transacoes"

CIDADES_BRASIL = [
    {"cidade": "Sao Paulo", "estado": "SP", "lat": -23.5505, "lon": -46.6333},
    {"cidade": "Rio de Janeiro", "estado": "RJ", "lat": -22.9068, "lon": -43.1729},
    {"cidade": "Belo Horizonte", "estado": "MG", "lat": -19.9167, "lon": -43.9345},
    {"cidade": "Recife", "estado": "PE", "lat": -8.0476, "lon": -34.8770},
    {"cidade": "Aracaju", "estado": "SE", "lat": -10.9472, "lon": -37.0731},
    {"cidade": "Brasilia", "estado": "DF", "lat": -15.7801, "lon": -47.9292}
]

def preparar_core_bancario_para_testes():
    """Garante que existem contas e cartões válidos na base de dados para o simulador usar."""
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Agencia (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, numero TEXT, endereco TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Cliente_Core (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Conta (numero TEXT PRIMARY KEY, saldo REAL, cliente_id INTEGER, agencia_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Cartao (numero TEXT PRIMARY KEY, limite REAL, tipo TEXT, conta_id TEXT)''')
    cursor.execute("SELECT numero FROM Conta")
    contas_db = cursor.fetchall()

    contas_validas = []
    cartoes_validos = {} 

    if not contas_db:
        print("⚙️ A preparar o Core Bancário com dados de teste...")

        cursor.execute("INSERT INTO Agencia (nome, numero, endereco) VALUES ('Sede', '0001', 'Avenida Central')")
        agencia_id = cursor.lastrowid

        for i in range(1, 51):
            cursor.execute("INSERT INTO Cliente_Core (nome, cpf) VALUES (?, ?)",
                           (f"Cliente Teste {i}", f"111222333{i:02d}"))
            cliente_id = cursor.lastrowid

            numero_conta = f"100{i}-X"
            cursor.execute("INSERT INTO Conta (numero, saldo, cliente_id, agencia_id) VALUES (?, ?, ?, ?)",
                           (numero_conta, random.uniform(1000, 50000), cliente_id, agencia_id))
            contas_validas.append(numero_conta)

            numero_cartao = f"500{i}-X"
            cursor.execute("INSERT INTO Cartao (numero, limite, tipo, conta_id) VALUES (?, ?, ?, ?)",
                           (numero_cartao, random.uniform(500, 10000), "credito", numero_conta))
            
            cartoes_validos[numero_conta] = numero_cartao

        conexao.commit()
        print("✅ Core Bancário pronto! Foram geradas 50 contas e cartões.")
    else:
        contas_validas = [conta[0] for conta in contas_db]
        
        cursor.execute("""
            SELECT c.numero, ca.numero 
            FROM Conta c
            JOIN Cartao ca ON c.numero = ca.conta_id
        """)
        for conta, cartao in cursor.fetchall():
            cartoes_validos[conta] = cartao

    conexao.close()
    return contas_validas, cartoes_validos


def iniciar_simulador():
    contas, cartoes = preparar_core_bancario_para_testes()

    if not contas:
        print("❌ Erro: Não há contas no banco de dados para simular.")
        return

    print("🚀 A iniciar o envio de transações hiper-realistas...")
    
    while True:
        conta_escolhida = random.choice(contas)
        tipo = random.choice(["pix", "cartao_credito", "cartao_debito", "transferencia"])

        if tipo in ["cartao_credito", "cartao_debito"]:
            dispositivo = cartoes.get(conta_escolhida, "app_mobile")
        else:
            dispositivo = random.choice(["app_mobile", "caixa_eletronico", "internet_banking", "web"])

        agora = datetime.now()
        local = random.choice(CIDADES_BRASIL)

        dados_transacao = {
            "valor": round(random.uniform(5.0, 5000.0), 2),
            "data": agora.strftime("%Y-%m-%d"),
            "hora": agora.strftime("%H:%M"),
            "dia_semana": agora.strftime("%A"),
            "latitude": local["lat"],
            "longitude": local["lon"],
            "tentativas": random.randint(1, 2),
            "tipo_transacao": tipo,
            "dispositivo": dispositivo,
            "cidade": local["cidade"],
            "estado": local["estado"],
            "pais": "Brasil",
            "categoria": random.choice(["alimentacao", "eletronicos", "servicos", "lazer", "vestuario", "saude"]),
            "conta": conta_escolhida
        }

        if random.random() < 0.10:
            dados_transacao["valor"] = round(random.uniform(12000.0, 28000.0), 2)
            dados_transacao["hora"] = f"{random.randint(1, 4):02d}:{random.randint(0, 59):02d}" 
            dados_transacao["tentativas"] = random.randint(5, 9)

        try:
            resposta = requests.post(URL_API, json=dados_transacao)
            
            if dados_transacao["valor"] > 10000:
                print(f"[{resposta.status_code}] 🚨 Anomalia enviada: {conta_escolhida} | {tipo} | R${dados_transacao['valor']}")
            else:
                print(f"[{resposta.status_code}] ✅ Transação Normal: {conta_escolhida} | {tipo} | R${dados_transacao['valor']}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro ao conectar com a API: A API está ligada no uvicorn?")

        time.sleep(0.2) 


if __name__ == "__main__":
    try:
        iniciar_simulador()
    except KeyboardInterrupt:
        print("\n🛑 Simulador parado pelo usuário.")