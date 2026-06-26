from __future__ import annotations

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.fraude_service import (
    conectar,
    conta_esta_bloqueada,
    inicializar_tabelas_fraude,
    marcar_conta_bloqueada,
    processar_transacao,
    registrar_notificacao,
)
from app.services.ia_service import analisar_transacao_ia, aplicar_resultado_ia_na_transacao

router = APIRouter(prefix="/monitoramento", tags=["🚨 Monitoramento em Tempo Real"])


class OpcoesDispositivo(str, Enum):
    web = "web"
    app_mobile = "app_mobile"
    caixa_eletronico = "caixa_eletronico"


class OpcoesTipoTransacao(str, Enum):
    pix = "pix"
    transferencia = "transferencia"
    credito = "credito"
    debito = "debito"


class OpcoesCategoria(str, Enum):
    transporte = "transporte"
    vestuario = "vestuario"
    lazer = "lazer"
    educacao = "educacao"
    saude = "saude"
    moradia = "moradia"
    alimentacao = "alimentacao"
    servicos = "servicos"
    supermercado = "supermercado"
    veiculos = "veiculos"
    eletronicos = "eletronicos"


def processar_vigilancia_ia(transacao_id: int) -> None:
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        row = conexao.execute("SELECT * FROM transactions WHERE id = ?", (transacao_id,)).fetchone()
        if not row:
            return

        transacao = dict(row)
        resultado_ia = analisar_transacao_ia(transacao)
        decisao = aplicar_resultado_ia_na_transacao(conexao, transacao_id, resultado_ia, conta=transacao.get("conta"))

        if decisao["bloqueio_por_ia"]:
            marcar_conta_bloqueada(
                conexao,
                str(transacao.get("conta")),
                resultado_ia["motivo"],
                transacao_id,
                "IA - Isolation Forest",
            )
            registrar_notificacao(
                conexao,
                "Bloqueio por IA",
                f"Conta {transacao.get('conta')} bloqueada por anomalia crítica na transação {transacao_id}.",
                transacao_id,
                str(transacao.get("conta")),
            )

        conexao.commit()


@router.post("/vigiar")
def monitorar_nova_transacao(
    conta: str,
    valor: float,
    cidade: str,
    dispositivo: OpcoesDispositivo,
    tipo_transacao: OpcoesTipoTransacao,
    categoria: OpcoesCategoria,
    background_tasks: BackgroundTasks,
):
    agora = datetime.now()
    data_atual = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M")
    dia_semana = agora.strftime("%A")

    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)

        if conta_esta_bloqueada(conexao, conta):
            raise HTTPException(
                status_code=403,
                detail=f"Operação recusada. A conta {conta} encontra-se bloqueada por suspeita de fraude.",
            )

        cursor = conexao.cursor()
        cursor.execute(
            """
            INSERT INTO transactions
                (conta, valor, data, hora, dispositivo, tipo_transacao, categoria, cidade,
                 latitude, longitude, tentativas, estado, pais, dia_semana)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conta,
                valor,
                data_atual,
                hora_atual,
                dispositivo.value,
                tipo_transacao.value,
                categoria.value,
                cidade,
                0,
                0,
                1,
                "PE",
                "Brasil",
                dia_semana,
            ),
        )
        transacao_id = cursor.lastrowid
        processamento = processar_transacao(conexao, transacao_id)
        conexao.commit()

    background_tasks.add_task(processar_vigilancia_ia, transacao_id)

    return {
        "status": "Transação registrada no monitoramento e enviada para análise da IA.",
        "transacao_id": transacao_id,
        "motor_fraude": processamento,
    }
