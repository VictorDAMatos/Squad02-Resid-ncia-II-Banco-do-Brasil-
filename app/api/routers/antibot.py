from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/antibot", tags=["🤖 Sistema Anti-Bot"])

def formatar_tempo(minutos_totais: float) -> str:
    #  Converte uma quantidade de minutos em minutos, horas, dias, meses ou anos
    minutos_totais = round(minutos_totais)
    
    if minutos_totais < 60:
        return f"{minutos_totais} minuto(s)"
    
    horas = minutos_totais // 60
    minutos_restantes = minutos_totais % 60
    if horas < 24:
        return f"{horas} hora(s) e {minutos_restantes} minuto(s)"
    
    dias = horas // 24
    if dias < 30:
        return f"{dias} dia(s)"
    
    meses = dias // 30
    if meses < 12:
        return f"{meses} mês(es)"
    
    anos = meses // 12
    return f"{anos} ano(s)"

@router.get("/verificar")
def verificar_velocidade_transacao(conta: str):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    # Busca as duas últimas transações mais recentes
    cursor.execute("""
        SELECT data, hora 
        FROM transactions 
        WHERE conta = ? 
        ORDER BY data DESC, hora DESC 
        LIMIT 2
    """, (conta,))
    
    transacoes = cursor.fetchall()
    conexao.close()

    if len(transacoes) < 2:
        return {
            "conta": conta,
            "status": "Regular",
            "mensagem": "Histórico insuficiente para análise de velocidade (menos de 2 transações)."
        }

    t1_info = dict(transacoes[0])
    t2_info = dict(transacoes[1])

    formato = "%Y-%m-%d %H:%M"
    
    try:
        hora1 = t1_info['hora'][:5]
        hora2 = t2_info['hora'][:5]

        timestamp_atual = datetime.strptime(f"{t1_info['data']} {hora1}", formato)
        timestamp_anterior = datetime.strptime(f"{t2_info['data']} {hora2}", formato)
        
        # Calcula a diferença total em minutos
        diferenca_minutos = abs((timestamp_atual - timestamp_anterior).total_seconds()) / 60.0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o tempo do banco: {e}")

    # Transforma os minutos brutos em texto legível
    tempo_formatado = formatar_tempo(diferenca_minutos)

    # ANTI-BOT: Se acontecer mais de uma transação no intervalo de 30 segundos
    if diferenca_minutos <= 0.5:
        return {
            "conta": conta,
            "status": "CRÍTICO - ALERTA DE FRAUDE",
            "motivo": "Múltiplas operações detectadas em curtíssimo intervalo de tempo. Comportamento típico de Bot.",
            "intervalo_detectado": tempo_formatado
        }
    
    return {
        "conta": conta,
        "status": "Regular",
        "mensagem": f"Intervalo seguro entre as transações avaliado em {tempo_formatado}."
    }