import sqlite3
import json

def carregar_dados_reais():
    conexao = sqlite3.connect('banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    print("Lendo o arquivo JSON")

    try:

        with open('transacoes_treino.json', 'r', encoding='utf-8') as ficheiro:
            transacoes = json.load(ficheiro)

        print(f"Encontradas {len(transacoes)} transações. Inserindo no banco, aguarde...")

        # Inserindo os dados
        for t in transacoes:
            cursor.execute('''
                INSERT INTO transactions (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                t.get('valor', 0.0),
                t.get('data', ''),
                t.get('hora', ''),
                t.get('categoria', ''),
                t.get('conta', ''),
                t.get('cidade', ''),
                t.get('tipo_transacao', 'N/A'), # Pega o tipo, se não tiver salva N/A
                t.get('dispositivo', 'N/A')     # Pega o dispositivo, se não tiver salva N/A
            ))

        conexao.commit()
        print("Concluído! Banco de dados populado com sucesso com os dados reais.")

    except FileNotFoundError:
        print("Erro: O arquivo 'transacoes_treino.json' não foi encontrado na pasta do PyCharm.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        conexao.close()

if __name__ == "__main__":
    carregar_dados_reais()