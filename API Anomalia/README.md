
# 🏦 API Banco do Brasil - Deteção de Fraudes (Squad 02)

Esta é uma API desenvolvida em **FastAPI** com base de dados **SQLite**, projetada para registar transações bancárias, filtrá-las e detetar possíveis anomalias/fraudes utilizando regras de negócio específicas. O projeto também conta com um módulo de atendimento via IA e um motor de geração de dados em tempo real.

## 🚀 Tecnologias Utilizadas
* **Python 3.10+**
* **FastAPI** (Framework da API)
* **Uvicorn** (Servidor ASGI)
* **SQLite3** (Base de Dados Relacional otimizada com Índices)
* **Scalar** (Documentação Visual Premium)

---

## ⚙️ Como executar o projeto localmente

### 1. Preparar o ambiente
Recomendamos o uso de um ambiente virtual para isolar as dependências do projeto.
No terminal, execute:
```bash
python -m venv venv
source venv/bin/activate  # No Linux/Mac
# ou venv\Scripts\activate no Windows
````

### 2. Instalar dependências e Iniciar a API 🟢

Com o ambiente ativado, pode instalar todas as bibliotecas necessárias e arrancar o servidor com um único comando. As bases de dados `.sqlite` serão criadas automaticamente caso não existam.

Bash

```
pip install fastapi uvicorn pydantic requests && python main.py
```

_(Dica de dev: Se quiser executar com recarregamento automático sempre que guardar o código, substitua o final por `uvicorn main:app --reload`)_

### 3. Aceder à Documentação Oficial

Com a API a correr, abra o seu navegador e aceda ao endereço abaixo para testar todos os endpoints pela interface visual: 👉 **https://www.google.com/search?q=http://127.0.0.1:8000/scalar**

---

## 🎲 Como popular a Base de Dados

Para testar a API, tem duas opções de injeção de dados:

**Opção A: Base de Dados Histórica (Dataset Oficial)** Num novo terminal (lembre-se de ativar o ambiente virtual nele também), execute o script abaixo para carregar as 30.000 transações exigidas para a avaliação:

Bash

```
python popular_banco.py
```

**Opção B: 🚀 Bónus - Simulador em Tempo Real** Criámos um motor infinito que gera transações aleatórias (com 10% de probabilidade de fraude) e envia-as para a API ao vivo. Excelente para testar a deteção de anomalias em tempo real e o limite de stress da API:

Bash

```
python simulador_realtime.py
```

---

## 🔍 Regras de Deteção de Anomalias Implementadas

O nosso endpoint `/anomalies` avalia 3 regras de risco (limitado aos 100 casos mais recentes para evitar bloqueios do navegador):

1. **Regra de Valor:** Transações com valor acima de R$ 10.000,00.
    
2. **Regra de Horário:** Transações realizadas de madrugada (00:00 às 05:00).
    
3. **Regra de Dispositivo:** Transações em Caixa Eletrónico acima de R$ 5.000,00.
    
