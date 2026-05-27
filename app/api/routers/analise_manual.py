from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.fraude_service import (
    agora,
    buscar_transacao,
    calcular_risco,
    conectar,
    conta_esta_bloqueada,
    desbloquear_conta_manual,
    enriquecer_transacao,
    inicializar_tabelas_fraude,
    linha_para_dict,
    processar_todas_transacoes,
    registrar_justificativa,
    registrar_notificacao,
    tabela_existe,
    atualizar_caso_manual,
    marcar_conta_bloqueada,
)

router = APIRouter(prefix="/analise", tags=["Análise Manual 4.1 a 4.12"])


class AcaoAnalise(BaseModel):
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


class BloqueioConta(BaseModel):
    conta: str = Field(..., min_length=1)
    transacao_id: int = Field(..., gt=0)
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


class DesbloqueioConta(BaseModel):
    conta: str = Field(..., min_length=1)
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


class InjecaoSaldo(BaseModel):
    conta: str = Field(..., min_length=1)
    valor: float = Field(..., gt=0)
    justificativa: str = Field(..., min_length=3)
    analista: str = "Analista"


def montar_perfil_dispositivo(conexao, conta: Optional[str] = None) -> list[dict]:
    params = []
    filtro = ""
    if conta:
        filtro = "WHERE conta = ?"
        params.append(conta)

    rows = conexao.execute(
        f"""
        SELECT conta, dispositivo, cidade,
               COUNT(*) AS total_uso,
               MIN(data || ' ' || hora) AS primeiro_uso,
               MAX(data || ' ' || hora) AS ultimo_uso,
               AVG(valor) AS valor_medio,
               MAX(valor) AS maior_valor
        FROM transactions
        {filtro}
        GROUP BY conta, dispositivo, cidade
        ORDER BY total_uso DESC, maior_valor DESC
        LIMIT 100
        """,
        params,
    ).fetchall()

    perfis = []
    for row in rows:
        item = linha_para_dict(row)
        if item["total_uso"] >= 5:
            confiavel = "Sim"
        elif item["total_uso"] >= 2:
            confiavel = "Parcial"
        else:
            confiavel = "Não"
        item["confiavel"] = confiavel
        perfis.append(item)
    return perfis


@router.get("/dashboard")
def dashboard():
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        processar_todas_transacoes(conexao)
        total_transacoes = conexao.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        total_bloqueadas = conexao.execute("SELECT COUNT(*) FROM contas_bloqueadas WHERE status = 'Bloqueada'").fetchone()[0]
        total_notificacoes = conexao.execute("SELECT COUNT(*) FROM logs_notificacoes").fetchone()[0]
        total_pendentes = conexao.execute("SELECT COUNT(*) FROM transactions WHERE status_transacao IN ('pendente', 'em análise')").fetchone()[0]
        sla_rows = conexao.execute(
            """
            SELECT aberto_em, atualizado_em
            FROM analise_casos
            WHERE atualizado_em IS NOT NULL
            """
        ).fetchall()

    tempos = []
    for row in sla_rows:
        inicio = datetime.fromisoformat(row["aberto_em"])
        fim = datetime.fromisoformat(row["atualizado_em"])
        tempos.append(max(1, round((fim - inicio).total_seconds() / 60)))

    return {
        "totalTransacoes": total_transacoes,
        "totalBloqueadas": total_bloqueadas,
        "totalNotificacoes": total_notificacoes,
        "totalPendentes": total_pendentes,
        "slaMedio": round(sum(tempos) / len(tempos)) if tempos else 0,
    }


@router.get("/transacoes")
def listar_transacoes(
    risco: str = Query("Todos", pattern="^(Todos|Baixo|Médio|Medio|Alto)$"),
    limite: int = Query(100, ge=1, le=500),
):
    risco_normalizado = "Médio" if risco == "Medio" else risco
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        processar_todas_transacoes(conexao)
        rows = conexao.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limite,)).fetchall()

        resultado = []
        for row in rows:
            transacao = linha_para_dict(row)
            risco_transacao = calcular_risco(transacao)
            if risco_normalizado != "Todos" and risco_transacao["nivel"] != risco_normalizado:
                continue
            resultado.append(enriquecer_transacao(conexao, transacao))

    return {"total": len(resultado), "transacoes": resultado}


@router.get("/transacoes/{transacao_id}")
def visualizar_transacao(transacao_id: int):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        transacao = buscar_transacao(conexao, transacao_id)
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        item = enriquecer_transacao(conexao, transacao)
        item["perfil_dispositivo"] = montar_perfil_dispositivo(conexao, transacao.get("conta"))
    return item


@router.post("/transacoes/{transacao_id}/confirmar")
def confirmar_suspeita(transacao_id: int, dados: AcaoAnalise):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        transacao = buscar_transacao(conexao, transacao_id)
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        atualizar_caso_manual(conexao, transacao_id, "Confirmada como suspeita", "Confirmada", dados.analista, dados.justificativa)
        registrar_justificativa(conexao, "Confirmação de suspeita", dados.justificativa, dados.analista, transacao_id, transacao.get("conta"))
        registrar_notificacao(conexao, "Alerta", f"Transação {transacao_id} confirmada como suspeita.", transacao_id, transacao.get("conta"))
        conexao.commit()
    return {"mensagem": "Transação confirmada como suspeita"}


@router.post("/transacoes/{transacao_id}/aprovar")
def aprovar_transacao(transacao_id: int, dados: AcaoAnalise):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        transacao = buscar_transacao(conexao, transacao_id)
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        atualizar_caso_manual(conexao, transacao_id, "Aprovada", "Aprovada", dados.analista, dados.justificativa)
        registrar_justificativa(conexao, "Aprovação manual", dados.justificativa, dados.analista, transacao_id, transacao.get("conta"))
        registrar_notificacao(conexao, "Aprovação", f"Transação {transacao_id} aprovada manualmente.", transacao_id, transacao.get("conta"))
        conexao.commit()
    return {"mensagem": "Transação aprovada manualmente"}


@router.post("/contas/bloquear")
def bloquear_conta(dados: BloqueioConta):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        transacao = buscar_transacao(conexao, dados.transacao_id)
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        if str(transacao.get("conta")) != dados.conta:
            raise HTTPException(status_code=400, detail="A conta informada não corresponde à transação")

        marcar_conta_bloqueada(conexao, dados.conta, dados.justificativa, dados.transacao_id, dados.analista)
        atualizar_caso_manual(conexao, dados.transacao_id, "Conta bloqueada", "Bloqueada", dados.analista, dados.justificativa)
        registrar_justificativa(conexao, "Bloqueio de conta", dados.justificativa, dados.analista, dados.transacao_id, dados.conta)
        registrar_notificacao(conexao, "Bloqueio", f"Conta {dados.conta} bloqueada.", dados.transacao_id, dados.conta)
        conexao.commit()
    return {"mensagem": "Conta bloqueada com sucesso"}


@router.get("/contas/bloqueadas")
def listar_contas_bloqueadas():
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        rows = conexao.execute("SELECT * FROM contas_bloqueadas WHERE status = 'Bloqueada' ORDER BY id DESC").fetchall()
    return {"bloqueadas": [linha_para_dict(row) for row in rows]}


@router.post("/contas/desbloquear")
def desbloquear_conta(dados: DesbloqueioConta):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        if not conta_esta_bloqueada(conexao, dados.conta):
            raise HTTPException(status_code=404, detail="Conta bloqueada não encontrada")
        desbloquear_conta_manual(conexao, dados.conta, dados.justificativa, dados.analista)
        conexao.commit()
    return {"mensagem": "Conta desbloqueada com sucesso"}


@router.post("/saldo/injetar")
def injetar_saldo(dados: InjecaoSaldo):
    aplicado = 0
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        if tabela_existe(conexao, "Conta"):
            atualizacao = conexao.execute(
                "UPDATE Conta SET saldo = saldo + ? WHERE numero = ?",
                (dados.valor, dados.conta),
            )
            aplicado = 1 if atualizacao.rowcount > 0 else 0

        conexao.execute(
            """
            INSERT INTO saldo_injecoes
                (data_hora, conta, valor, justificativa, analista, aplicado_na_tabela_conta)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (agora(), dados.conta, dados.valor, dados.justificativa, dados.analista, aplicado),
        )
        registrar_justificativa(conexao, "Injeção de saldo", f"Valor R$ {dados.valor:.2f}. Motivo: {dados.justificativa}", dados.analista, None, dados.conta)
        registrar_notificacao(conexao, "Saldo", f"Saldo injetado/registrado na conta {dados.conta}.", None, dados.conta)
        conexao.commit()

    return {"mensagem": "Injeção de saldo registrada", "saldo_aplicado_na_tabela_conta": bool(aplicado)}


@router.get("/logs/justificativas")
def listar_justificativas(limite: int = Query(100, ge=1, le=500)):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        rows = conexao.execute("SELECT * FROM logs_justificativas ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    return {"logs": [linha_para_dict(row) for row in rows]}


@router.get("/logs/notificacoes")
def listar_notificacoes(limite: int = Query(100, ge=1, le=500)):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        rows = conexao.execute("SELECT * FROM logs_notificacoes ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    return {"logs": [linha_para_dict(row) for row in rows]}


@router.get("/dispositivos")
def listar_dispositivos(conta: Optional[str] = None):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        perfis = montar_perfil_dispositivo(conexao, conta)
    return {"dispositivos": perfis}


@router.get("/sla")
def listar_sla():
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        rows = conexao.execute("SELECT * FROM analise_casos ORDER BY id DESC").fetchall()

    casos = []
    for row in rows:
        caso = linha_para_dict(row)
        fim = caso.get("atualizado_em") or agora()
        inicio_dt = datetime.fromisoformat(caso["aberto_em"])
        fim_dt = datetime.fromisoformat(fim)
        tempo_minutos = max(1, round((fim_dt - inicio_dt).total_seconds() / 60))
        caso["tempo_minutos"] = tempo_minutos
        caso["sla_status"] = "Dentro do prazo" if tempo_minutos <= 30 else "Atrasado"
        casos.append(caso)

    return {"casos": casos}


@router.get("/timeline/{transacao_id}")
def listar_timeline_transacao(transacao_id: int):
    with conectar() as conexao:
        inicializar_tabelas_fraude(conexao)
        transacao = buscar_transacao(conexao, transacao_id)
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        conta = transacao.get("conta")
        historico = conexao.execute(
            """
            SELECT id, data, hora, valor, categoria, cidade, tipo_transacao, dispositivo
            FROM transactions
            WHERE conta = ?
            ORDER BY data DESC, hora DESC
            LIMIT 10
            """,
            (conta,),
        ).fetchall()
        justificativas = conexao.execute(
            """
            SELECT data_hora, acao, justificativa
            FROM logs_justificativas
            WHERE transacao_id = ? OR conta = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (transacao_id, conta),
        ).fetchall()
        notificacoes = conexao.execute(
            """
            SELECT data_hora, tipo, mensagem, status
            FROM logs_notificacoes
            WHERE transacao_id = ? OR conta = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (transacao_id, conta),
        ).fetchall()
        transacao_enriquecida = enriquecer_transacao(conexao, transacao)

    eventos = [
        {
            "momento": f"{row['data']} {row['hora']}",
            "tipo": "Transação",
            "descricao": f"{row['tipo_transacao']} de R$ {row['valor']:.2f} em {row['cidade']} via {row['dispositivo']}.",
        }
        for row in historico
    ]
    eventos.extend({"momento": row["data_hora"], "tipo": row["acao"], "descricao": row["justificativa"]} for row in justificativas)
    eventos.extend({"momento": row["data_hora"], "tipo": row["tipo"], "descricao": f"{row['mensagem']} Status: {row['status']}."} for row in notificacoes)

    return {"transacao": transacao_enriquecida, "conta": conta, "eventos": eventos}
