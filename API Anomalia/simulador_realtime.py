import time
import requests
import random
from datetime import datetime, timedelta

URL_API = "http://127.0.0.1:8000/transactions"

# Listas dos dados que podem ser gerados
CIDADES = ["Recife", "São Paulo", "Rio de Janeiro", "Salvador", "Belo Horizonte", "Fortaleza", "Curitiba", "Manaus",
           "Brasília", "Porto Alegre", "Aracaju"]
CATEGORIAS = ["alimentacao", "eletronicos", "saude", "lazer", "vestuario", "transporte", "servicos"]
TIPOS = ["pix", "cartao_credito", "cartao_debito", "transferencia"]
DISPOSITIVOS = ["app_mobile", "maquininha_pos", "caixa_eletronico", "internet_banking"]


def gerar_transacao_aleatoria():
    # Aplica 10% de chance de gerar uma transação fraudulenta
    is_fraude = random.random() < 0.10

    if is_fraude:
        # Gera valores absurdos e horários do périodo da madrugada (Ativando as Regras)
        valor = round(random.uniform(11000.0, 50000.0), 2)
        hora = f"0{random.randint(0, 4)}:{random.randint(10, 59)}"
    else:
        # Transação normal
        valor = round(random.uniform(5.0, 3000.0), 2)
        hora = f"{random.randint(6, 23):02d}:{random.randint(10, 59)}"

    # Gera uma data aleatória dos últimos 30 dias
    dias_atras = random.randint(0, 30)
    data_transacao = datetime.now() - timedelta(days=dias_atras)

    return {
        "valor": valor,
        "data": data_transacao.strftime("%Y-%m-%d"),
        "hora": hora,
        "categoria": random.choice(CATEGORIAS),
        "conta": f"{random.randint(10000, 99999)}-{random.randint(0, 9)}",
        "cidade": random.choice(CIDADES),
        "tipo_transacao": random.choice(TIPOS),
        "dispositivo": random.choice(DISPOSITIVOS)
    }


def iniciar_gerador():
    print("🚀 Iniciando Motor de Transações Aleatórias Infinitas...")
    print("Pressione Ctrl+C para parar a qualquer momento.\n")

    contador = 0
    while True:
        try:
            payload = gerar_transacao_aleatoria()

            # Encaminha para a API principal
            resposta = requests.post(URL_API, json=payload)

            if resposta.status_code == 201:
                contador += 1
                status = "🚨 ANOMALIA" if payload["valor"] > 10000 or int(payload["hora"][:2]) < 5 else "✅ OK"
                print(
                    f"[{contador}] {status} | R$ {payload['valor']:8.2f} | {payload['cidade']} | {payload['categoria']}")
            else:
                print(f"⚠️ Erro da API: {resposta.text}")

            # Espera entre 1 a três segundos antes de gerar mais
            time.sleep(random.uniform(0.5, 1.5))

        except requests.exceptions.ConnectionError:
            print("❌ ERRO: A sua API (main.py) não está ligada! Inicie o servidor em outro terminal.")
            break
        except KeyboardInterrupt:
            # Captura o Ctrl+C para parar graciosamente
            print(f"\n🛑 Motor parado pelo usuário. Total de {contador} transações geradas.")
            break


if __name__ == "__main__":
    iniciar_gerador()