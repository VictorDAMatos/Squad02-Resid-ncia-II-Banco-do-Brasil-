# Integração completa do módulo do Analista

## Objetivo

Este pacote deixa o módulo do analista integrado com o backend e com o frontend, usando uma única API FastAPI e um único painel em:

```text
http://127.0.0.1:8000/static/analista/dashboard.html
```

A documentação também pode ser aberta em:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/scalar
```

## O que foi corrigido nesta versão

- Removida a duplicação de `app.include_router(transacoes.router)` no `app/main.py`.
- Adicionada rota `/health` para testar rapidamente se a API está online.
- Mantida a rota `/scalar` com a documentação visual da API.
- Corrigido o caminho do banco no repository do analista para usar caminho absoluto baseado na pasta do projeto.
- Alterado `API_BASE_URL` do frontend para `window.location.origin`, evitando travar em `http://127.0.0.1:8000` quando a porta ou host mudar.
- Corrigida a renderização da tabela de anomalias, que antes dependia de um elemento que não existia na tela.
- Adicionadas telas e ações no frontend para cobrir as rotas principais do backend do analista.
- Criado `requirements.txt` básico com `fastapi` e `uvicorn[standard]`.

## Funcionalidades disponíveis no painel

O painel agora possui menus para:

- Painel Geral e KPIs.
- Transações suspeitas.
- Filtro de transações por CPF/conta, categoria, valor e risco.
- Detalhe manual da transação.
- Processamento do fluxo de confirmação.
- Lista de contas bloqueadas.
- Desbloqueio de conta com justificativa.
- Linha do tempo do suspeito.
- Registro e listagem de notificações.
- Injeção de saldo de teste.
- Painel de SLA.
- Resolução de análise manual com justificativa.
- Logs operacionais.
- Auditoria.

## Rotas principais integradas

- `GET /analista/resumo`
- `GET /analista/anomalias-detalhadas`
- `GET /analista/categorias`
- `GET /analista/transacoes-filtradas`
- `GET /analista/transacoes-por-risco`
- `GET /analista/transacoes/{transacao_id}`
- `POST /analista/transacoes/{transacao_id}/processar-fluxo`
- `GET /analista/contas-bloqueadas`
- `POST /analista/desbloquear/{conta_id}`
- `GET /analista/suspeitos/{suspeito}/timeline`
- `POST /analista/notificacoes`
- `GET /analista/notificacoes`
- `POST /analista/injetar-saldo`
- `GET /analista/sla`
- `POST /analista/sla/{transacao_id}/resolver`
- `GET /registros/logs`
- `GET /registros/auditoria`

## Como executar

Na raiz do projeto, instale as dependências:

```bash
pip install -r requirements.txt
```

Depois rode:

```bash
python -m uvicorn app.main:app --reload
```

Acesse:

```text
http://127.0.0.1:8000/static/analista/dashboard.html
```

## Autenticação do analista

O backend protege as rotas do analista usando o header:

```text
X-Analista-Token: analista-dev-token
```

O frontend já envia esse token automaticamente.

Para produção, configure a variável de ambiente:

```bash
ANALISTA_API_TOKEN="seu-token-seguro"
```

Para desativar temporariamente a proteção em ambiente local:

```bash
ANALISTA_AUTH_DISABLED=true
```

## Validação realizada

Foram testadas com sucesso as seguintes rotas em ambiente local:

- `/health`
- `/openapi.json`
- `/scalar`
- `/static/analista/dashboard.html`
- `/static/analista/js/api_analista.js`
- `/analista/resumo`
- `/analista/anomalias-detalhadas`
- `/analista/categorias`
- `/analista/transacoes-filtradas?limite=3`
- `/analista/transacoes-por-risco?risco=alto&limite=3`
- `/analista/transacoes/{id}`
- `/analista/transacoes/{id}/processar-fluxo`
- `/analista/contas-bloqueadas`
- `/analista/suspeitos/{suspeito}/timeline`
- `/analista/notificacoes`
- `/analista/injetar-saldo`
- `/analista/sla`

Também foi executado:

```bash
python -m compileall app
```
