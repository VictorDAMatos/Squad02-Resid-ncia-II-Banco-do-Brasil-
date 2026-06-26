from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.fraude_service import (
    conectar,
    conta_esta_bloqueada,
    enriquecer_transacao,
    inicializar_tabelas_fraude,
    linha_para_dict,
    marcar_conta_bloqueada,
    processar_transacao,
    registrar_notificacao,
    iniciar_sla_transacao,
)
from app.services.ia_service import analisar_transacao_ia, aplicar_resultado_ia_na_transacao

router = APIRouter(prefix="/transacoes", tags=["Core Bancário & Transações"])


class Transacao(BaseModel):
    valor: float = Field(..., gt=0)
    data: str
    hora: str
    categoria: str
    conta: str
    cidade: str
    tipo_transacao: str
    dispositivo: str

    # Campos opcionais usados pelo modelo de IA antigo.
    latitude: float = 0
    longitude: float = 0
    tentativas: int = 1
    estado: str = "PE"
    pais: str = "Brasil"
    dia_semana: Optional[str] = None


def _dia_semana_padrao(data: str) -> str:
    try:
        return datetime.fromisoformat(data[:10]).strftime("%A")
    except Exception:
        return datetime.now().strftime("%A")


@router.post("/")
def criar_transacao(transacao: Transacao):
    dados = transacao.model_dump()
    dados["dia_semana"] = dados.get("dia_semana") or _dia_semana_padrao(dados["data"])

    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)

        if conta_esta_bloqueada(conexao, transacao.conta):
            raise HTTPException(
                status_code=403,
                detail="Conta bloqueada por suspeita de fraude até revisão do analista.",
            )

        resultado_ia = analisar_transacao_ia(dados)

        cursor = conexao.cursor()
        cursor.execute(
            """
            INSERT INTO transactions
                (valor, data, hora, categoria, conta, cidade, tipo_transacao, dispositivo,
                 latitude, longitude, tentativas, estado, pais, dia_semana)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                transacao.latitude,
                transacao.longitude,
                transacao.tentativas,
                transacao.estado,
                transacao.pais,
                dados["dia_semana"],
            ),
        )
        transacao_id = cursor.lastrowid

        # Mantém o motor determinístico já existente no projeto avançado.
        processamento = processar_transacao(conexao, transacao_id)

        # A IA atua como camada complementar e eleva o risco quando necessário.
        decisao_ia = aplicar_resultado_ia_na_transacao(
            conexao,
            transacao_id,
            resultado_ia,
            conta=transacao.conta,
        )

        # O SLA precisa considerar a decisão final depois da IA.
        # Antes, o SLA só era criado pelo motor determinístico; quando o motor dava verde
        # mas a IA elevava para amarelo/EM_ANALISE, o painel continuava vazio.
        classificacao_final = str(decisao_ia.get("classificacao_final") or "").lower()
        status_final = str(decisao_ia.get("status_transacao_final") or "").lower()
        status_ia = str(decisao_ia.get("status_ia") or "").upper()
        if (
            classificacao_final in {"amarelo", "vermelho"}
            or status_final in {"pendente", "em análise", "em_analise"}
            or status_ia == "EM_ANALISE"
        ):
            iniciar_sla_transacao(
                conexao,
                transacao_id,
                "alto" if classificacao_final == "vermelho" else "medio",
            )

        if decisao_ia["bloqueio_por_ia"]:
            marcar_conta_bloqueada(
                conexao,
                transacao.conta,
                resultado_ia["motivo"],
                transacao_id,
                "IA - Isolation Forest",
            )
            registrar_notificacao(
                conexao,
                "Bloqueio por IA",
                f"A IA detectou anomalia crítica na transação {transacao_id} e bloqueou a conta {transacao.conta}.",
                transacao_id,
                transacao.conta,
            )

        conexao.commit()

    return {
        "mensagem": "Transação registrada, monitorada e analisada pela IA.",
        "id": transacao_id,
        "ia": resultado_ia,
        "motor_fraude": {
            "classificacao_risco": processamento["risco"]["classificacao"],
            "nivel_risco": processamento["risco"]["nivel"],
            "pontos_risco": processamento["risco"]["pontos"],
            "motivo_risco": processamento["risco"]["motivo"],
            "status_transacao": processamento["status_transacao"],
            "status_conta": processamento["status_conta"],
            "bloqueio_automatico": processamento["bloqueio_automatico"],
        },
        "decisao_final": decisao_ia,
    }


@router.get("/")
def listar_transacoes(
    conta: Optional[str] = None,
    limite: int = Query(200, ge=1, le=1000),
):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        query = "SELECT * FROM transactions"
        params: list[object] = []

        if conta:
            query += " WHERE conta = ?"
            params.append(conta)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limite)

        rows = conexao.execute(query, params).fetchall()
        return [enriquecer_transacao(conexao, linha_para_dict(row)) for row in rows]
