from fastapi import APIRouter, HTTPException, BackgroundTasks
import sqlite3
from datetime import datetime
from enum import Enum

from app.api.routers.risco import classificar
from app.api.routers.status import listar_status_conta, classificar_status_transacao

router = APIRouter(prefix="/monitoramento", tags=["🚨 Monitoramento em Tempo Real"])

# Opções fixas para o Dispositivo
class OpcoesDispositivo(str, Enum):
    web = "web"
    app_mobile = "app_mobile"
    caixa_eletronico = "caixa eletrônico"

# Opções fixas para o Tipo de Transação
class OpcoesTipoTransacao(str, Enum):
    pix = "pix"
    transferencia = "transferência"
    cartao_credito = "cartao_credito"
    cartao_debito = "cartao_debito"

# Opções fixas para a Categoria
class OpcoesCategoria(str, Enum):
    transporte = "transporte"
    vestuario = "vestuario"
    lazer = "lazer"
    educacao = "educacao"
    saude = "saude"
    moradia = "moradia"
    alimentacao = "alimentacao"


def processar_vigilancia(transacao_id: int, conta: str, valor: float, hora: str, dispositivo: str, cidade: str):
    print(f"\n[VIGILÂNCIA REAL-TIME] Analisando risco da transação {transacao_id}...")

    transacao_dict = {
        "valor": valor,
        "hora": hora,
        "dispositivo": dispositivo
    }

    # 1. Executa a sua função classificação de risco (retorna a cor)
    cor_risco, motivo_risco = classificar(transacao_dict)

    # 2. Usa a função do status para descobrir o status em formato de texto ('pendente', 'em análise', 'aprovada')
    dados_para_status = {"classificacao_risco": cor_risco}
    status_transacao_final = classificar_status_transacao(dados_para_status)

    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    try:
        colunas_verificacao = ["classificacao_risco", "motivo_risco", "status_transacao"]
        for coluna in colunas_verificacao:
            try:
                cursor.execute(f"ALTER TABLE transactions ADD COLUMN {coluna} TEXT")
            except sqlite3.OperationalError:
                pass

        # 3. Atualiza a transação com todos os dados
        cursor.execute("""
            UPDATE transactions 
            SET classificacao_risco = ?, motivo_risco = ?, status_transacao = ?
            WHERE id = ?
        """, (cor_risco, motivo_risco, status_transacao_final, transacao_id))
        
        conexao.commit()
        conexao.close() 

        print(f"📌 [ROBÔ] Transação {transacao_id} finalizada como {cor_risco.upper()} -> Status: {status_transacao_final}")

        # 4. Aciona o recálculo das contas
        print("[ESTEIRA] Acionando recálculo de status oficial da conta (status.py)...")
        listar_status_conta()
        
        print("✅ [VIGILÂNCIA] Processamento em segundo plano concluído.\n")

    except Exception as e:
        print(f"❌ [ERRO VIGILÂNCIA] Falha ao processar esteira de segurança: {e}")
        try:
            conexao.close()
        except:
            pass


@router.post("/vigiar")
def monitorar_nova_transacao(
    conta: str, 
    valor: float, 
    cidade: str, 
    dispositivo: OpcoesDispositivo, 
    tipo_transacao: OpcoesTipoTransacao,
    categoria: OpcoesCategoria,     
    background_tasks: BackgroundTasks
):
    conexao = sqlite3.connect('data/banco_brasil_transacoes.sqlite')
    cursor = conexao.cursor()

    agora = datetime.now()
    data_atual = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M")

    novas_colunas = ["dispositivo", "tipo_transacao", "categoria", "cidade", "status_transacao", "status_conta", "classificacao_risco", "motivo_risco"]
    for col_teste in novas_colunas:
        try:
            cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_teste} TEXT")
        except sqlite3.OperationalError:
            pass

    # SEGURANÇA: Bloqueia na hora se a conta já estiver marcada como Bloqueada
    cursor.execute("""
        SELECT status_conta FROM transactions 
        WHERE conta = ? AND status_conta IS NOT NULL 
        ORDER BY id DESC LIMIT 1
    """, (conta,))
    resultado_conta = cursor.fetchone()
    
    if resultado_conta and resultado_conta[0] == "Bloqueada":
        conexao.close()
        raise HTTPException(
            status_code=403, 
            detail=f"Operação Recusada. A conta {conta} encontra-se BLOQUEADA por suspeita de fraude."
        
    transacao_dict = {
        "valor": valor,
        "hora": hora_atual,
        "dispositivo": dispositivo.value
    }
    
    cor_risco, motivo_risco = classificar(transacao_dict)
    
    dados_para_status = {"classificacao_risco": cor_risco}
    status_transacao_real = classificar_status_transacao(dados_para_status)
    # ----------------------------------------------------------------------

    try:
        cursor.execute("PRAGMA table_info(transactions)")
        colunas_info = cursor.fetchall()
        
        # Dados salvos da conta
        dados_para_salvar = {
            "conta": conta,
            "valor": valor,
            "data": data_atual,
            "hora": hora_atual,
            "dispositivo": dispositivo.value,
            "tipo_transacao": tipo_transacao.value,
            "categoria": categoria.value,
            "cidade": cidade,
            "classificacao_risco": cor_risco,
            "motivo_risco": motivo_risco,
            "status_transacao": status_transacao_real
        }
        
        for col in colunas_info:
            nome_coluna = col[1]
            tipo_coluna = col[2].upper()
            eh_obrigatoria = col[3]
            valor_padrao = col[4]
            
            if col[5] == 1:
                continue
                
            if eh_obrigatoria and (nome_coluna not in dados_para_salvar) and (valor_padrao is None):
                if "INT" in tipo_coluna or "REAL" in tipo_coluna or "NUM" in tipo_coluna:
                    dados_para_salvar[nome_coluna] = 0
                else:
                    dados_para_salvar[nome_coluna] = "N/A"

        colunas_finais = list(dados_para_salvar.keys())
        valores_finais = list(dados_para_salvar.values())
        paragrafos_interrogacao = ", ".join(["?"] * len(colunas_finais))
        str_colunas = ", ".join(colunas_finais)

        query_dinamica = f"INSERT INTO transactions ({str_colunas}) VALUES ({paragrafos_interrogacao})"
        
        cursor.execute(query_dinamica, valores_finais)
        conexao.commit()

    except Exception as e:
        conexao.close()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no banco: {e}")

    conexao.close()

    background_tasks.add_task(listar_status_conta)

    return {
        "status": "Transação processada com sucesso!",
        "detalhes": dados_para_salvar
    }
