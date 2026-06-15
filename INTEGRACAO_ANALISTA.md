# Integração Front + Back do Analista

## O que foi integrado

- O backend do analista foi refatorado para a arquitetura em camadas:
  - `app/api/routers/analista.py`
  - `app/services/analista_service.py`
  - `app/repositories/analista_repository.py`
  - `app/schemas/analista_schema.py`
- O frontend do painel do analista foi ajustado para consumir os endpoints refatorados.
- Foi mantida compatibilidade com os dados retornados pelo backend, especialmente nos agrupamentos dos gráficos, que agora usam o campo `nome`.
- O caminho do banco no repository foi corrigido para funcionar independentemente do diretório de execução.

## Endpoints usados pelo frontend

- `GET /analista/resumo`
- `GET /analista/anomalias-detalhadas`
- `GET /analista/categorias`
- `GET /analista/transacoes-filtradas`
- `GET /registros/logs`
- `GET /registros/auditoria`

## Como rodar

Na raiz do projeto:

```bash
uvicorn app.main:app --reload
```

Depois acesse:

```text
http://127.0.0.1:8000/static/analista/dashboard.html
```

## Arquivos principais alterados

- `app/api/routers/analista.py`
- `app/services/analista_service.py`
- `app/repositories/analista_repository.py`
- `app/schemas/analista_schema.py`
- `frontend/analista/js/api_analista.js`
- `app/api/__init__.py`
- `app/api/routers/__init__.py`
- `app/services/__init__.py`
- `app/repositories/__init__.py`
- `app/schemas/__init__.py`
