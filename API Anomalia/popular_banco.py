import sqlite3
import random
from datetime import datetime, timedelta

def gerar_dados_falsos(quantidade=1000):
    # Conecta ao banco de dados que o main.py criou
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    # Listas de opções para o nosso gerador aleatório
    categorias = ['alimentacao', 'transporte', 'saude', 'educacao', 'lazer', 'moradia', 'vestuario']
    cidades = ['Recife', 'Sao Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Aracaju', 'Curitiba']
    tipos = ['pix', 'cartao_credito', 'cartao_debito', 'transferencia']
    dispositivos = ['app_mobile', 'web', 'caixa_eletronico']

    print(f"Gerando {quantidade} transações fictícias. Aguarde...")

    for _ in range(quantidade):
        # LÓGICA DE ANOMALIAS: 5% de chance da transação ser uma fraude de propósito para o teste
        is_anomalia = random.random() < 0.05

        if is_anomalia:
            # Gera um valor gigante ou horário suspeito
            valor = round(random.uniform(10500.0, 50000.0), 2)
            hora = f"0{random.randint(0, 4)}:{random.randint(10, 59)}" # Entre 00:00 e 04:59
        else:
            # Transação perfeitamente normal
            valor = round(random.uniform(10.0, 3000.0), 2)
            hora = f"{random.randint(6, 23):02d}:{random.randint(10, 59)}"

        # Gera uma data aleatória nos últimos 90 dias
        dias_atras = random.randint(0, 90)
        data_transacao = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')

        # Escolhe itens aleatórios das listas
        categoria = random.choice(categorias)
        conta = f"{random.randint(10000, 99999)}-{random.randint(0, 9)}"
        cidade = random.choice(cidades)
        tipo_transacao = random.choice(tipos)
        dispositivo = random.choice(dispositivos)

        # Salva no banco de dados
        cursor.execute('''
            INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (valor, data_transacao, hora, categoria, conta, cidade, tipo_transacao, dispositivo))

    conexao.commit()
    conexao.close()
    print("Sucesso! Banco de dados populado e pronto para testes.")

if __name__ == "__main__":
    # Você pode mudar de 1000 para 30000 se quiser simular o requisito exato do professor!
    gerar_dados_falsos(1000)