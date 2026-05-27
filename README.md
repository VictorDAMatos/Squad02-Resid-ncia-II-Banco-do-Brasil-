# 🏦 Sistema Bancário & Motor de Detecção de Fraudes

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)

Este projeto é uma API RESTful desenvolvida em **FastAPI** que simula a infraestrutura de backend de um banco real. Ele é composto por dois grandes módulos que se comunicam perfeitamente: um **Core Bancário** (gestão de clientes, contas e cartões) e um **Motor de Fraudes** (análise de transações e detecção de anomalias).

---

## ✨ Arquitetura e Diferenciais do Projeto

O sistema foi construído seguindo rigorosas boas práticas de Engenharia de Software e Banco de Dados:

* **Integridade Relacional (Zero Dados Fantasmas):** Diferente de APIs de simulação simples, este sistema exige que uma Conta e um Cartão existam fisicamente no banco de dados antes de aceitar uma transação.
* **Validação de Negócio (Status HTTP Corretos):** Tentativas de transações com contas inexistentes retornam erro `404 Not Found`, e uso de cartões não vinculados à conta retornam `403 Forbidden`.
* **Motor de Fraudes Inteligente (SQL Avançado):** A rota de anomalias utiliza `LEFT JOIN` para cruzar a tabela de transações com os dados do Core Bancário, devolvendo ao analista de segurança não apenas o valor da fraude, mas o **Nome e CPF** do cliente suspeito.
* **Geração de Dados Massiva e Idempotente:** O script de histórico (`popular_banco.py`) limpa registros antigos e utiliza o comando `executemany` do SQLite para inserir 30.000 transações perfeitamente interligadas em menos de 1 segundo.

---

## 🛠️ Estrutura do Banco de Dados (SQLite)

O banco de dados relacional (`banco_brasil_transacoes.sqlite`) é gerado automaticamente e possui a seguinte hierarquia:

1. **Agencia:** Possui ID, nome, número e endereço.
2. **Cliente_Core:** Possui ID, nome e CPF.
3. **Conta:** Vinculada a um Cliente e a uma Agência. Possui saldo.
4. **Cartao:** Vinculado a uma Conta.
5. **Transactions:** O registro da movimentação financeira. Só é salva após validação rigorosa contra a tabela de Contas e Cartões.

---

## 🚀 Passo a Passo para Rodar o Projeto

### 1. Preparando o Ambiente Certifique-se de ter o Python instalado. Instale as bibliotecas necessárias rodando o comando no terminal:

```
pip install fastapi uvicorn requests
```

### 2. Iniciando a API (Core Bancário)

Para ligar o servidor FastAPI, execute o arquivo principal (supondo que ele se chame `main.py`):

```
uvicorn main:app --reload
```

A API estará rodando em: `http://127.0.0.1:8000`
### 3. Gerando o Histórico de Dados (Massivo)

Com a API rodando, abra um **novo terminal** e execute o script de popular o banco. Ele criará 100 clientes reais e injetará 30.000 transações não duplicadas:

```
python popular_banco.py
```

_Vá até a rota `/anomalies` na API e veja o Motor de Fraudes cruzando os dados e detectando movimentações suspeitas!_

### 4. Iniciando o Simulador em Tempo Real

Para simular o uso diário do banco (clientes passando o cartão pelo país), execute o simulador. Ele usa as contas válidas recém-criadas e dispara requisições via `POST /transactions`:

```
python simulador_realtime.py
```

---

## 📌 Principais Endpoints

### 💲 Core Bancário

- `POST /agencias` - Cria uma nova agência bancária.
    
- `POST /cartoes` - Emite um cartão e o vincula a uma conta existente.
    

### 💳 Transações Bancárias

- `POST /transactions` - Registra uma transação (Valida se a conta e cartão existem primeiro).
    
- `GET /transactions` - Lista transações com suporte a filtros (categoria, cidade, valores).
    
- `GET /transactions/{id}` - Busca os detalhes de um comprovante específico.
    

### 🚨 Segurança e Anomalias

- `GET /anomalies` - Retorna transações suspeitas enriquecidas com Nome e CPF do cliente, baseadas em 3 regras de negócio (Madrugada, Valores Altos e Saques em Caixa Eletrônico).
  
## 🔍 Regras de Deteção de Anomalias Implementadas

O nosso endpoint `/anomalies` cruza os dados das transações com o Core Bancário (via `JOIN`) para devolver o **Nome e o CPF** do cliente suspeito. Ele avalia 3 regras de risco principais:

- **Regra de Valor:** Transações com valor acima de R$ 10.000,00.
    
- **Regra de Horário:** Transações realizadas de madrugada (00:00 às 05:00).
    
- **Regra de Dispositivo:** Transações em Caixa Eletrónico acima de R$ 5.000,00.