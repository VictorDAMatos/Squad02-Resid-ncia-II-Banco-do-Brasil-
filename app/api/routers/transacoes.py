from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.inference.predictor import prever

from app.services.fraude_service import (
    conectar,
    conta_esta_bloqueada,
    enriquecer_transacao,
    inicializar_tabelas_fraude,
    linha_para_dict,
    processar_transacao,
)

router = APIRouter(
    prefix="/transacoes",
    tags=["Core Bancário + IA"]
)

# ==================================================
# SCHEMA
# ==================================================

class Transacao(BaseModel):

    valor: float = Field(..., gt=0)

    data: str
    hora: str

    categoria: str
    conta: str

    cidade: str

    tipo_transacao: str
    dispositivo: str

    # IA
    latitude: float = 0
    longitude: float = 0

    tentativas: int = 1

    estado: str = "SE"
    pais: str = "Brasil"

    dia_semana: str = "Tuesday"

# ==================================================
# CRIAR TRANSAÇÃO
# ==================================================

@router.post("/")
def criar_transacao(transacao: Transacao):

    dados = transacao.dict()

    # ==================================================
    # IA ANALISA
    # ==================================================

    resultado_ia = prever(dados)

    with conectar() as conexao:

        inicializar_tabelas_fraude(conexao)

        # ==================================================
        # CONTA BLOQUEADA
        # ==================================================

        if conta_esta_bloqueada(conexao, transacao.conta):

            raise HTTPException(
                status_code=403,
                detail="Conta bloqueada pela IA até revisão do analista."
            )

        # ==================================================
        # BLOQUEIO IA
        # ==================================================

        status_transacao = "APROVADA"

        if resultado_ia["risco"] == 2:
            status_transacao = "EM_ANALISE"

        elif resultado_ia["risco"] == 3:
            status_transacao = "BLOQUEADA"

        # ==================================================
        # INSERIR TRANSAÇÃO
        # ==================================================

        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO transactions
                (
                    valor,
                    data,
                    hora,
                    categoria,
                    conta,
                    cidade,
                    tipo_transacao,
                    dispositivo
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transacao.valor,
                transacao.data,
                transacao.hora,
                transacao.categoria,
                transacao.conta,
                transacao.cidade,
                transacao.tipo_transacao,
                transacao.dispositivo,
            ),
        )

        transacao_id = cursor.lastrowid

        # ==================================================
        # MOTOR DE FRAUDE LEGADO
        # ==================================================

        processamento = processar_transacao(
            conexao,
            transacao_id
        )

        conexao.commit()

    # ==================================================
    # RESPOSTA FINAL
    # ==================================================

    return {

        "mensagem": "Transação registrada e analisada com sucesso!",

        "id": transacao_id,

        # ==================================================
        # IA
        # ==================================================

        "ia": {
            "anomalia": resultado_ia["anomalia"],
            "score": resultado_ia["score"],
            "risco": resultado_ia["risco"],
            "motivo": resultado_ia["motivo"],
        },

        # ==================================================
        # MOTOR DE FRAUDE
        # ==================================================

        "motor_fraude": {

            "classificacao_risco": processamento["risco"]["classificacao"],

            "nivel_risco": processamento["risco"]["nivel"],

            "pontos_risco": processamento["risco"]["pontos"],

            "motivo_risco": processamento["risco"]["motivo"],

            "status_transacao": processamento["status_transacao"],

            "status_conta": processamento["status_conta"],

            "bloqueio_automatico": processamento["bloqueio_automatico"],
        },

        # ==================================================
        # DECISÃO FINAL
        # ==================================================

        "status_final": status_transacao
    }

# ==================================================
# LISTAR TRANSAÇÕES
# ==================================================

@router.get("/")
def listar_transacoes(
    conta: Optional[str] = None,
    limite: int = 200
):

    with conectar() as conexao:

        inicializar_tabelas_fraude(conexao)

        query = "SELECT * FROM transactions"

        params = []

        if conta:
            query += " WHERE conta = ?"
            params.append(conta)

        query += " ORDER BY id DESC LIMIT ?"

        params.append(limite)

        rows = conexao.execute(query, params).fetchall()

        transacoes = [

            enriquecer_transacao(
                conexao,
                linha_para_dict(row)
            )

            for row in rows
        ]

    return transacoes