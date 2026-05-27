<<<<<<< HEAD
from fastapi import APIRouter

from app.services.fraude_service import conectar, processar_todas_transacoes

router = APIRouter(prefix="/status", tags=["✅ Status de Transação e Conta"])


@router.get("/Transacao")
def listar_status_transacoes():
    with conectar() as conexao:
        resultados = processar_todas_transacoes(conexao)

    return [
        {
            "transacao_id": item["transacao_id"],
            "conta": item["conta"],
            "classificacao_risco": item["risco"]["classificacao"],
            "nivel_risco": item["risco"]["nivel"],
            "transacao_status": item["status_transacao"],
        }
        for item in resultados
    ]


@router.get("/Conta")
def listar_status_conta():
    with conectar() as conexao:
        resultados = processar_todas_transacoes(conexao)

    contas = {}
    for item in resultados:
        conta = item["conta"]
        if conta not in contas:
            contas[conta] = {
                "conta": conta,
                "status": item["status_conta"],
                "total_vermelhos": 0,
                "total_amarelos": 0,
                "total_verdes": 0,
                "bloqueio_automatico": item["bloqueio_automatico"],
                "motivo_bloqueio": item["motivo_bloqueio"],
            }

        cor = item["risco"]["classificacao"]
        if cor == "vermelho":
            contas[conta]["total_vermelhos"] += 1
        elif cor == "amarelo":
            contas[conta]["total_amarelos"] += 1
        else:
            contas[conta]["total_verdes"] += 1

        if item["status_conta"] == "Bloqueada":
            contas[conta]["status"] = "Bloqueada"
        if item["bloqueio_automatico"]:
            contas[conta]["bloqueio_automatico"] = True
            contas[conta]["motivo_bloqueio"] = item["motivo_bloqueio"]

    return list(contas.values())
=======
from fastapi import APIRouter
import sqlite3
from app.api.routers.risco import classificar

router = APIRouter(prefix="/status", tags=["✅ Status de Transação e Conta"])

def classificar_status_transacao(t):
    cor = t['classificacao_risco']

    # --- PENDENTE ---
    if cor == 'vermelho':
        return 'pendente'
    
    # --- EM ANALISE ---
    if cor == 'amarelo':
        return 'em análise'
    
    # --- APROVADA ---
    return 'aprovada'

@router.get("/Transacao")
def listar_status_transacoes():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    # --- Criar coluna de status de transaçao ---
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN status_transacao TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT id, conta, classificacao_risco FROM transactions")
    rows = cursor.fetchall()

    resultado_transacao = []

    for row in rows:
        t = dict(row)

        statusTransacao = classificar_status_transacao(t)

        cursor.execute('''
            UPDATE transactions 
            SET status_transacao = ? 
            WHERE id = ?
        ''', (statusTransacao, t['id']))


        # --- Transação ---
        resultado_transacao.append({
            'transacao_id': t['id'],
            'conta': t['conta'],
            'transacao_status': statusTransacao
        })

    conexao.commit()
    conexao.close()

    return resultado_transacao

@router.get("/Conta")
def listar_status_conta():
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    # --- Criar coluna de status de conta ---
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN status_conta TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT conta, classificacao_risco FROM transactions")
    rows = cursor.fetchall()
    
    contagem_contas = {}

    for row in rows:
        t = dict(row)
        n_conta = t['conta']
        cor = t['classificacao_risco']

        # --- Adiciona a contagem_contas ---
        if n_conta not in contagem_contas:
            contagem_contas[n_conta] = {"amarelo": 0, "vermelho": 0, "verde": 0}

        # --- Soma +1 na cor ---
        if cor in contagem_contas[n_conta]:
            contagem_contas[n_conta][cor] += 1

    resultado_final = []
    for conta in contagem_contas:
        cores = contagem_contas[conta]
        
        # --- Coloca statua da conta: ativa ou bloqueada ---
        if cores["vermelho"] > 0 or cores["amarelo"] > 2:
            status_final = "Bloqueada"
        else:
            status_final = "Ativa"
        
        cursor.execute('''
            UPDATE transactions 
            SET status_conta = ? 
            WHERE conta = ?
        ''', (status_final, conta))

        # --- Retorna conta, status e qnt de cores ---
        resultado_final.append({
            "conta": conta,
            "status": status_final,
            "total_vermelhos": cores["vermelho"],
            "total_amarelos": cores["amarelo"],
            "total_verdes": cores["verde"]
        })

    conexao.commit()
    conexao.close()

    return resultado_final
>>>>>>> cfce345ebedc0fae6774daa52362edc1076d114b
