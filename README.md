# API Banco do Brasil - Sistema de Detecção de Anomalias Financeiras

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)
# Sobre o Projeto

Este projeto foi desenvolvido como atividade acadêmica do curso de Sistemas de Informação, com foco em Arquitetura de Software, Inteligência Artificial, Engenharia de Dados e Segurança de Sistemas.

A solução simula um ambiente bancário capaz de processar operações financeiras, monitorar transações em tempo real e identificar possíveis fraudes por meio da combinação de regras de negócio e técnicas de Machine Learning.

O sistema foi projetado para auxiliar analistas de fraude na identificação de comportamentos suspeitos, reduzindo o tempo de análise e aumentando a precisão na classificação de riscos.

---

# Objetivo

Detectar possíveis fraudes financeiras através da combinação de:

- Regras de negócio;
- Monitoramento transacional;
- Inteligência Artificial baseada em Isolation Forest;
- Sistema de classificação de risco;
- Dashboard para analistas;
- Auditoria de operações.

---

# Principais Funcionalidades

## Core Bancário

- Cadastro de clientes;
- Consulta de clientes;
- Gestão de contas;
- Operações bancárias simuladas.

## Transações

- PIX;
- Transferências;
- Depósitos.

## Inteligência Artificial

- Detecção automática de anomalias;
- Análise comportamental de transações;
- Geração de score de risco;
- Classificação automática de risco;
- Identificação de padrões suspeitos.

## Monitoramento de Fraudes

- Monitoramento em tempo real;
- Registro de ocorrências;
- Análise de eventos suspeitos;
- Alertas para analistas.

## Auditoria

- Histórico de operações;
- Registro de ações;
- Logs de acesso;
- Rastreabilidade das análises.

## Dashboard do Analista

- Visualização de alertas;
- Estatísticas de risco;
- Indicadores operacionais;
- Relatórios de fraude.

---

# Arquitetura da Solução

A arquitetura segue um fluxo orientado a eventos, onde toda transação financeira passa por um processo automatizado de monitoramento e análise.

## Fluxo Principal

Cliente → Transação → Monitoramento → IA (Isolation Forest) → Análise de Anomalia → Classificação de Risco → Dashboard

---

# Participação da Inteligência Artificial

A Inteligência Artificial atua diretamente após o registro das transações financeiras.

As seguintes operações são enviadas automaticamente para análise:

- PIX
- Transferências
- Depósitos

Após o recebimento da transação, o sistema realiza uma avaliação comportamental para identificar desvios em relação ao padrão esperado do cliente.

---

# Problema Resolvido pela IA

Soluções baseadas apenas em regras fixas possuem limitações para detectar novos padrões de fraude.

A utilização de Machine Learning permite identificar comportamentos anômalos que não seriam encontrados apenas por regras tradicionais.

Isso possibilita:

- Maior capacidade de detecção;
- Redução de falsos positivos;
- Análise automática de grandes volumes de dados;
- Maior eficiência operacional.

---

# Benefícios da Solução

- Detecção automática de anomalias;
- Redução de falsos positivos;
- Classificação automática de risco;
- Automação da análise;
- Monitoramento em tempo real;
- Apoio à tomada de decisão dos analistas;
- Escalabilidade para grandes volumes de transações.

---

# Inteligência Artificial

O projeto utiliza o algoritmo Isolation Forest da biblioteca Scikit-Learn para identificar padrões incomuns em transações financeiras.

## Modelo Utilizado

- Isolation Forest
- Aprendizado não supervisionado
- Detecção de anomalias

O algoritmo isola observações consideradas raras ou diferentes do comportamento predominante, atribuindo um score de anomalia para cada transação.

---

## Variáveis Analisadas

A IA avalia múltiplos fatores durante a análise:

- Valor da transação;
- Categoria da operação;
- Localização;
- Dispositivo utilizado;
- Quantidade de tentativas;
- Horário da transação;
- Histórico comportamental do cliente.

---

# Modelo de Avaliação de Risco

A solução utiliza uma abordagem híbrida composta por:

- Regras de negócio;
- Inteligência Artificial (Isolation Forest).

Essa combinação permite unir conhecimento de domínio bancário com técnicas estatísticas de detecção de anomalias.

---

## Pesos Utilizados

|Critério|Peso|
|---|---|
|Valor|30%|
|Localização|20%|
|Dispositivo|15%|
|Tentativas|15%|
|Horário|10%|
|IA (Isolation Forest)|10%|

---

# Score de Anomalia

O Isolation Forest gera um score que representa o nível de anormalidade da transação.

Quanto mais distante do comportamento normal, maior será o risco associado.

### Exemplos

| Score | Interpretação      |
| ----- | ------------------ |
| -0.01 | Normal             |
| -0.10 | Atenção            |
| -0.30 | Altamente suspeito |

---

# Classificação de Risco

## Risco 1

Baixa probabilidade de fraude.

Critério:

Score > -0.10

---

## Risco 2

Comportamento suspeito que exige monitoramento.

Critério:

-0.10 ≥ Score ≥ -0.25

---

## Risco 3

Alta probabilidade de fraude.

Critério:

Score < -0.25

---

# Composição do Risco Final

A classificação final não depende exclusivamente da Inteligência Artificial.

O cálculo considera:

- Resultado das regras de negócio;
- Score gerado pelo Isolation Forest;
- Indicadores de comportamento transacional.

Dessa forma, o sistema produz uma avaliação mais robusta e confiável do risco associado à operação.

---

# Resultado da Análise

A IA gera os seguintes indicadores:

- ia_score
- ia_anomalia
- ia_risco
- ia_motivo

Esses dados são utilizados pelo Dashboard para exibição dos alertas e apoio à tomada de decisão.

---

# Estrutura do Projeto

```
app/

├── ai/
│   ├── inference/
│   ├── models/
│   └── training/
│
├── api/
│   └── routers/
│
├── services/
├── models/
├── schemas/
├── core/
│
└── main.py
```

---

# Endpoints Principais

## Inteligência Artificial

```
POST /ia/analisar
```

```
POST /ia/analisar-anomalia
```

```
GET /ia/dashboard
```

```
GET /ia/relatorio-fraudes
```

---

## Transações

```
POST /transacoes
```

```
GET /transacoes
```

---

## Monitoramento

```
GET /monitoramento
```

---

## Dashboard do Analista

```
GET /analista/dashboard
```

---

# Tecnologias Utilizadas

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic

## Inteligência Artificial

- Scikit-Learn
- Isolation Forest
- NumPy
- Pandas
- Joblib

## Banco de Dados

- SQLite

## Documentação

- Swagger UI
- OpenAPI

---

# Instalação

## Criar ambiente virtual

```
python -m venv .venv
```

## Ativar ambiente virtual

### Windows

```
.venv\Scripts\activate
```

### Linux

```
source .venv/bin/activate
```

## Instalar dependências

```
pip install fastapi uvicorn sqlalchemy pydantic requests pandas numpy scikit-learn joblib python-multipart
```

---

# Execução

Executar API:

```
python -m uvicorn app.main:app --reload
```

Executar simulador de transações:

```
python scripts\simulador_realtime.py
```

---

# Documentação da API

## Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

## OpenAPI

[http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---