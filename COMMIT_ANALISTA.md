# Commit da integração do analista

Este pacote já está com a integração do front do analista com o backend do analista.

## Arquivos principais alterados

- `app/main.py`
  - adiciona `StaticFiles` para abrir o frontend em `/static/...`.
- `app/repositories/analista_repository.py`
  - ajusta o caminho do banco usando o diretório raiz do projeto.
- `frontend/analista/js/api_analista.js`
  - centraliza chamadas no backend com `fetchAnalista`.
  - mantém os cabeçalhos de auditoria `X-Analista-ID` e `X-Analista-Nome`.
  - adapta os gráficos para o formato retornado pelo backend refatorado (`nome`, `qtd`, `volume`).
- `INTEGRACAO_ANALISTA.md`
  - resumo técnico da integração.

## Como testar

```bash
python -m uvicorn app.main:app --reload
```

Depois abra:

```text
http://127.0.0.1:8000/static/analista/dashboard.html
```

## Como commitar

```bash
git status
git add .
git commit -m "Integra front e back do analista"
git push
```
