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

# Principais Rotas da API

Abaixo estão listadas as principais rotas da API para execução, validação e demonstração do sistema. A documentação completa dos endpoints pode ser acessada automaticamente pelo Swagger em: `http://127.0.0.1:8000/docs`.

> Observação: as rotas protegidas do analista exigem o header `x-analista-token`.
>
> Token padrão para testes acadêmicos:
>
> ```txt
> x-analista-token: analista-dev-token
> ```

## Usuário

```http
GET /usuario/perfil
GET /usuario/saldo
GET /usuario/transacoes
GET /usuario/extrato/exportar
```

Rotas relacionadas ao perfil do usuário, saldo, histórico de movimentações e exportação do extrato.

---

## Operações Bancárias do Usuário

```http
POST /usuario/transferencia
POST /usuario/pix
POST /usuario/deposito
POST /usuario/boleto/gerar
POST /usuario/boleto/pagar
GET /usuario/boleto/listar
POST /usuario/emprestimo/simular
GET /usuario/emprestimo/listar
```

Rotas responsáveis pelas operações bancárias simuladas, como transferência, PIX, depósito, boleto e empréstimo.

---

## Transações

```http
POST /transacoes/
GET /transacoes/
GET /historico/transacoes
GET /analista/transacoes/{transacao_id}
GET /analista/transacoes-filtradas
GET /analista/transacoes-por-risco
POST /analista/transacoes/{transacao_id}/processar-fluxo
```

Rotas utilizadas para registrar, listar, consultar detalhes, filtrar e processar transações no fluxo do analista.

---

## Classificação, Monitoramento e Anti-Bot

```http
GET /classificacao/risco
POST /monitoramento/vigiar
GET /antibot/verificar
```

Rotas relacionadas à classificação de risco, monitoramento em tempo real e verificação de comportamento de velocidade/transações repetidas.

> A rota antiga `GET /monitoramento` não é o endpoint principal utilizado nesta versão. Para validação do monitoramento, utilize `POST /monitoramento/vigiar`.

---

## Inteligência Artificial

```http
POST /ia/analisar
POST /ia/analisar-anomalia
GET /ia/dashboard
GET /ia/relatorio-fraudes
GET /ia/anomalies
```

Rotas utilizadas para análise de anomalias, consulta de indicadores da IA, dashboard e relatórios relacionados à detecção de fraude.

---

## Analista

As rotas abaixo exigem o header:

```txt
x-analista-token: analista-dev-token
```

```http
GET /analista/resumo
GET /analista/anomalias-detalhadas
GET /analista/categorias
GET /analista/contas-bloqueadas
POST /analista/desbloquear/{conta_id}
POST /analista/injetar-saldo
GET /analista/suspeitos/{suspeito}/timeline
```

Rotas do painel do analista para resumo operacional, investigação de anomalias, contas bloqueadas, desbloqueio, injeção de saldo de teste e linha do tempo do suspeito.

---

## Notificações

```http
GET /analista/notificacoes
POST /analista/notificacoes
```

Rotas responsáveis pelo registro e consulta de notificações relacionadas a usuários ou transações suspeitas.

---

## SLA

```http
GET /analista/sla
POST /analista/sla/{transacao_id}/resolver
```

Rotas responsáveis por acompanhar o tempo de resposta das análises manuais e registrar a resolução feita pelo analista.

---

## Relatórios, Logs e Auditoria

```http
GET /registros/logs
GET /registros/auditoria
GET /ia/relatorio-fraudes
```

Rotas voltadas para rastreabilidade, registro de operações, auditoria e relatórios de fraude.

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

## 1. Entrar na pasta raiz do projeto

Antes de executar a API, o terminal precisa estar na pasta onde aparecem as pastas `app`, `frontend`, `database` e o arquivo `README.md`.

Exemplo no Windows:

```powershell
cd "C:\Users\Pedro\Downloads\Squad02_corrigido_saldo_sla_FINAL3\Squad02-Resid-ncia-II-Banco-do-Brasil--main"
```

Para conferir se está na pasta correta:

```powershell
dir
```

A saída deve mostrar algo parecido com:

```txt
app
frontend
database
README.md
```

> Não execute o projeto usando `python app/main.py`. O correto é iniciar pelo Uvicorn, pois o projeto usa imports internos a partir do pacote `app`.

---

## 2. Criar ambiente virtual

```powershell
python -m venv .venv
```

---

## 3. Ativar ambiente virtual

### Windows

```powershell
.venv\Scripts\activate
```

### Linux/Mac

```bash
source .venv/bin/activate
```

---

## 4. Instalar dependências

```powershell
pip install fastapi uvicorn pandas numpy scikit-learn joblib pydantic requests python-multipart
```

Caso o projeto seja executado em uma máquina limpa, instale as dependências antes de subir o servidor.

---

# Execução

## Comando padrão

```powershell
python -m uvicorn app.main:app --reload
```

Esse comando é válido para desenvolvimento, pois reinicia a API automaticamente quando algum arquivo é alterado.

## Comando alternativo para Windows/Python 3.14

Em algumas máquinas Windows, principalmente usando Python 3.14, o `--reload` pode gerar erro de multiprocessing. Nesse caso, execute sem `--reload`:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Depois de subir a API, acesse:

```txt
http://127.0.0.1:8000/docs
```

---

## Executar simulador de transações

Com a API rodando, abra outro terminal na pasta raiz do projeto e execute:

```powershell
python scripts\simulador_realtime.py
```

O simulador envia transações para a rota `POST /transacoes/` usando a mesma base SQLite da API: `data/banco_brasil_transacoes.sqlite`.

---

# Scripts Auxiliares

Os scripts auxiliares ficam na pasta `scripts/` e devem ser executados a partir da pasta raiz do projeto, onde aparecem as pastas `app`, `frontend`, `database`, `data` e o arquivo `README.md`.

## Popular banco de dados

```powershell
python scripts\popular_banco.py
```

Esse script popula a base SQLite com dados de teste. Ele utiliza o banco `data/banco_brasil_transacoes.sqlite`, o mesmo utilizado pela API.

## Simulador em tempo real

```powershell
python scripts\simulador_realtime.py
```

Esse script simula o envio contínuo de transações para a API. Para funcionar corretamente, a API precisa estar rodando em `http://127.0.0.1:8000`.

---

# Validação da Inteligência Artificial

A inferência da IA pode ser validada pelo script interno de teste:

```powershell
python -m app.ai.inference.test_predictor
```

Esse comando testa o carregamento do modelo Isolation Forest, dos encoders e do scaler, retornando a classificação de anomalia, score, risco e motivo.

Também é possível validar a IA pelas rotas disponíveis no Swagger:

```http
POST /ia/analisar
POST /ia/analisar-anomalia
GET /ia/dashboard
GET /ia/relatorio-fraudes
GET /ia/anomalies
```

---

# Observações de Teste

- A base SQLite pode conter dados de teste usados na validação do projeto.
- Os scripts auxiliares usam a mesma base da API: `data/banco_brasil_transacoes.sqlite`.
- O token `analista-dev-token` é utilizado apenas para demonstração acadêmica.
- O login visual do frontend é demonstrativo; as rotas protegidas do analista usam validação por header.
- O comando com `--reload` pode falhar em algumas instalações Windows/Python 3.14. Nesse caso, use o comando alternativo sem reload.

---

# Documentação da API

## Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

## OpenAPI

[http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---