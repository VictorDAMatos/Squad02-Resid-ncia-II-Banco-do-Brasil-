# API Banco do Brasil - Sistema de Detecção de Anomalias Financeiras

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)
## Sobre o Projeto

Este projeto foi desenvolvido como atividade acadêmica do curso de Sistemas de Informação com foco em Arquitetura de Software, Inteligência Artificial e Segurança de Sistemas.

A solução simula um ambiente bancário capaz de monitorar transações financeiras em tempo real, detectar comportamentos anômalos e classificar riscos utilizando regras de negócio e Inteligência Artificial.

---

## Objetivo

Detectar possíveis fraudes financeiras através da combinação de:

- Regras de negócio;
- Monitoramento transacional;
- Inteligência Artificial baseada em Isolation Forest;
- Sistema de classificação de risco;
- Dashboard para analistas.

---

## Principais Funcionalidades

### Core Bancário

- Cadastro de clientes
- Consulta de clientes
- Gestão de contas
- Operações bancárias

### Transações

- PIX
- Transferência
- Depósito

### Inteligência Artificial

- Detecção automática de anomalias
- Análise de comportamento transacional
- Geração de score de anomalia
- Classificação automática de risco

### Monitoramento de Fraudes

- Análise em tempo real
- Identificação de comportamentos suspeitos
- Registro de ocorrências

### Auditoria

- Registro de operações
- Histórico de ações
- Logs de acesso

### Dashboard do Analista

- Visualização de alertas
- Estatísticas de risco
- Relatórios de fraude
- Indicadores operacionais

---

# Arquitetura da Solução

Fluxo principal:

Cliente → Transação → Monitoramento → IA (Isolation Forest) → Score → Classificação de Risco → Dashboard do Analista

---

## Inteligência Artificial

O projeto utiliza o algoritmo Isolation Forest da biblioteca Scikit-Learn.

### Variáveis analisadas

- Valor da transação
- Categoria
- Localização
- Dispositivo
- Quantidade de tentativas
- Comportamento histórico

### Resultado da análise

A IA gera:

- ia_score
- ia_anomalia
- ia_risco
- ia_motivo

---

## Classificação de Risco

### Risco 1

Baixa probabilidade de fraude.

### Risco 2

Comportamento suspeito que exige monitoramento.

### Risco 3

Alta probabilidade de fraude.

---

## Estrutura do Projeto

app/

├── ai/

│ ├── inference/

│ ├── models/

│ └── training/

├── api/

│ └── routers/

├── services/

├── models/

├── schemas/

├── core/

└── main.py

---

## Endpoints Principais

### IA

POST /ia/analisar

POST /ia/analisar-anomalia

GET /ia/dashboard

GET /ia/relatorio-fraudes

### Transações

POST /transacoes

GET /transacoes

### Monitoramento

GET /monitoramento

### Analista

GET /analista/dashboard

---

## Tecnologias Utilizadas

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic

### Inteligência Artificial

- Scikit-Learn
- Isolation Forest
- NumPy
- Pandas
- Joblib

### Banco de Dados

- SQLite

### Documentação

- Swagger UI
- OpenAPI

---

## Instalação

Criar ambiente virtual:

```
python -m venv .venv
```

Ativar ambiente virtual:

Windows:

```
.venv\Scripts\activate
```

Instalar dependências:

```
pip install -r requirements.txt
```

Executar a aplicação:

```
python -m uvicorn app.main:app --reload
```

---

## Documentação da API

Swagger:

[http://localhost:8000/docs](http://localhost:8000/docs)

OpenAPI:

[http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---
