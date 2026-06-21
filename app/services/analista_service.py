"""Regras de negócio da área do analista.

Service = camada que decide o que deve ser feito.
Ela usa o repository para buscar/salvar dados e devolve algo pronto para a rota.
"""

from typing import Any

from app.repositories.analista_repository import AnalistaRepository


class AnalistaService:
    def __init__(self, repository: AnalistaRepository | None = None) -> None:
        self.repository = repository or AnalistaRepository()

    def obter_resumo(self) -> dict[str, Any]:
        return {
            "kpis": self.repository.buscar_kpis(),
            "por_categoria": self.repository.agrupar_com_volume("categoria"),
            "por_cidade": self.repository.agrupar_com_volume("cidade", limite=10),
            "por_dispositivo": self.repository.agrupar_quantidade("dispositivo"),
            "por_tipo": self.repository.agrupar_com_volume("tipo_transacao"),
            "por_hora": self.repository.agrupar_por_hora(),
            "ultimas_transacoes": self.repository.ultimas_transacoes(limite=10),
        }

    def _suspeito_da_transacao(self, transacao: dict[str, Any]) -> str:
        for campo in ("cpf", "conta", "conta_id", "id"):
            if transacao.get(campo) is not None:
                return str(transacao[campo])
        return "desconhecido"

    def calcular_risco(self, transacao: dict[str, Any]) -> dict[str, Any]:
        """Calcula as três intensidades de risco e a consequência automática.

        Regras simples e transparentes, fáceis de ajustar depois:
        - ALTO: bloqueia automaticamente;
        - MÉDIO: manda para análise manual;
        - BAIXO: aprova automaticamente.
        """
        valor = float(transacao.get("valor") or 0)
        hora = str(transacao.get("hora") or "")
        dispositivo = str(transacao.get("dispositivo") or "").lower()
        motivos: list[str] = []

        if valor > 10000:
            motivos.append("Valor muito alto, acima de R$ 10.000.")
        elif valor > 5000:
            motivos.append("Valor alto, acima de R$ 5.000.")

        if "00:00" <= hora <= "05:59":
            motivos.append("Transação realizada de madrugada.")

        if dispositivo == "caixa_eletronico" and valor > 5000:
            motivos.append("Saque alto em caixa eletrônico.")

        perfil_dispositivo = self.repository.buscar_historico_dispositivo(transacao)
        if perfil_dispositivo.get("disponivel") and perfil_dispositivo.get("total_transacoes_historicas", 0) > 0:
            if not perfil_dispositivo.get("dispositivo_ja_usado"):
                motivos.append("Dispositivo diferente do histórico do cliente.")

        if valor > 10000 or len(motivos) >= 3:
            intensidade = "alto"
            acao = "bloquear"
            status_transacao = "bloqueada"
            status_conta = "Bloqueada"
        elif motivos:
            intensidade = "medio"
            acao = "enviar_para_analise"
            status_transacao = "em_analise"
            status_conta = None
        else:
            intensidade = "baixo"
            acao = "aprovar"
            status_transacao = "aprovada"
            status_conta = None

        return {
            "intensidade": intensidade,
            "acao_automatica": acao,
            "status_transacao": status_transacao,
            "status_conta": status_conta,
            "motivos": motivos or ["Nenhuma regra crítica encontrada."],
        }

    def processar_fluxo_confirmacao(self, transacao_id: int) -> dict[str, Any]:
        transacao = self.repository.buscar_transacao_por_id(transacao_id)
        if not transacao:
            return {
                "transacao_id": transacao_id,
                "risco": "nao_encontrada",
                "acao_automatica": "nenhuma",
                "mensagem": "Transação não encontrada.",
                "transacao": {},
            }

        risco = self.calcular_risco(transacao)
        transacao_atualizada = self.repository.atualizar_fluxo_transacao(
            transacao_id=transacao_id,
            status_transacao=risco["status_transacao"],
            status_conta=risco["status_conta"],
        ) or transacao

        suspeito = self._suspeito_da_transacao(transacao)
        if risco["intensidade"] == "alto":
            self.repository.registrar_notificacao(
                suspeito=suspeito,
                transacao_id=transacao_id,
                mensagem="Transação bloqueada automaticamente por risco alto.",
                canal="sistema",
                analista="sistema",
            )
            self.repository.registrar_auditoria(
                entidade="transacao",
                entidade_id=transacao_id,
                acao="bloqueio_automatico",
                justificativa="; ".join(risco["motivos"]),
                analista="sistema",
            )
        elif risco["intensidade"] == "medio":
            self.repository.iniciar_analise_sla(transacao_id, risco["intensidade"])
            self.repository.registrar_notificacao(
                suspeito=suspeito,
                transacao_id=transacao_id,
                mensagem="Transação enviada para análise manual por risco médio.",
                canal="sistema",
                analista="sistema",
            )

        self.repository.registrar_auditoria(
            entidade="transacao",
            entidade_id=transacao_id,
            acao=f"fluxo_processado_{risco['intensidade']}",
            justificativa="; ".join(risco["motivos"]),
            analista="sistema",
        )

        return {
            "transacao_id": transacao_id,
            "risco": risco["intensidade"],
            "acao_automatica": risco["acao_automatica"],
            "mensagem": "Fluxo de confirmação processado com sucesso.",
            "transacao": {**transacao_atualizada, "risco_calculado": risco},
        }

    def listar_anomalias_detalhadas(self, limite: int = 50) -> list[dict[str, Any]]:
        return self.repository.listar_anomalias_detalhadas(limite=limite)

    def listar_categorias(self) -> dict[str, list[str]]:
        return {"categorias": self.repository.listar_categorias()}

    def listar_transacoes_por_risco(self, risco: str | None, limite: int) -> dict[str, Any]:
        risco_normalizado = risco.lower() if risco else None
        permitidos = {None, "baixo", "medio", "alto"}
        if risco_normalizado not in permitidos:
            return {
                "total": 0,
                "limite": limite,
                "transacoes": [],
                "avisos": ["Filtro de risco inválido. Use: baixo, medio ou alto."],
            }

        transacoes = self.repository.listar_transacoes_para_filtro_risco(limite=limite)
        enriquecidas = []
        for transacao in transacoes:
            risco_calculado = self.calcular_risco(transacao)
            item = {**transacao, "risco": risco_calculado}
            if risco_normalizado is None or risco_calculado["intensidade"] == risco_normalizado:
                enriquecidas.append(item)

        return {
            "total": len(enriquecidas),
            "limite": limite,
            "transacoes": enriquecidas,
            "avisos": [],
        }

    def obter_detalhe_transacao(self, transacao_id: int) -> dict[str, Any]:
        transacao = self.repository.buscar_transacao_por_id(transacao_id)
        if not transacao:
            return {
                "transacao": {},
                "risco": {"intensidade": "nao_encontrada", "motivos": ["Transação não encontrada."]},
                "perfil_dispositivo": {"disponivel": False, "mensagem": "Transação não encontrada."},
                "sla": None,
            }

        return {
            "transacao": transacao,
            "risco": self.calcular_risco(transacao),
            "perfil_dispositivo": self.repository.buscar_historico_dispositivo(transacao),
            "sla": self.repository.buscar_sla_transacao(transacao_id),
        }

    def listar_contas_bloqueadas(self) -> dict[str, Any]:
        bloqueadas = self.repository.listar_contas_bloqueadas()
        avisos: list[str] = []

        return {
            "total": len(bloqueadas),
            "bloqueadas": bloqueadas,
            "avisos": avisos,
        }

    def desbloquear_conta(self, conta_id: str, justificativa: str, analista: str) -> dict[str, str]:
        linhas_afetadas = self.repository.desbloquear_conta(conta_id)
        self.repository.registrar_auditoria(
            entidade="conta",
            entidade_id=conta_id,
            acao="desbloqueio",
            justificativa=justificativa,
            analista=analista,
        )

        if linhas_afetadas == 0:
            return {
                "mensagem": (
                    f"Justificativa registrada, mas nenhuma conta/transação foi atualizada para o identificador {conta_id}. "
                    "Verifique se a base possui status_conta e se o identificador está correto."
                )
            }

        return {"mensagem": f"Conta {conta_id} desbloqueada com sucesso. Justificativa registrada em auditoria."}

    def montar_timeline_suspeito(self, suspeito: str, limite: int = 100) -> dict[str, Any]:
        transacoes = self.repository.listar_transacoes_do_suspeito(suspeito, limite=limite)
        notificacoes = self.repository.listar_notificacoes(suspeito=suspeito, limite=limite)
        ids_auditoria = [suspeito, *[str(t.get("id")) for t in transacoes if t.get("id") is not None]]
        auditoria = self.repository.listar_auditoria_por_entidades(ids_auditoria, limite=limite)
        dispositivos = self.repository.listar_dispositivos_do_suspeito(suspeito)

        volume_total = sum(float(t.get("valor") or 0) for t in transacoes)
        maior_transacao = max([float(t.get("valor") or 0) for t in transacoes], default=0)
        riscos = [self.calcular_risco(t)["intensidade"] for t in transacoes]

        perfil = {
            "total_transacoes": len(transacoes),
            "volume_total": volume_total,
            "maior_transacao": maior_transacao,
            "qtd_risco_alto": riscos.count("alto"),
            "qtd_risco_medio": riscos.count("medio"),
            "qtd_risco_baixo": riscos.count("baixo"),
        }

        return {
            "suspeito": suspeito,
            "perfil": perfil,
            "transacoes": transacoes,
            "notificacoes": notificacoes,
            "auditoria": auditoria,
            "dispositivos": dispositivos,
        }

    def registrar_notificacao(self, suspeito: str, mensagem: str, canal: str, transacao_id: int | None, analista: str) -> dict[str, str]:
        notificacao_id = self.repository.registrar_notificacao(
            suspeito=suspeito,
            mensagem=mensagem,
            canal=canal,
            transacao_id=transacao_id,
            analista=analista,
        )
        return {"mensagem": f"Notificação registrada com sucesso. ID: {notificacao_id}."}

    def listar_notificacoes(self, suspeito: str | None, limite: int) -> dict[str, Any]:
        notificacoes = self.repository.listar_notificacoes(suspeito=suspeito, limite=limite)
        return {"total": len(notificacoes), "notificacoes": notificacoes}

    def injetar_saldo(self, conta: str, valor: float, justificativa: str, analista: str) -> dict[str, str]:
        injecao_id = self.repository.registrar_injecao_saldo(conta, valor, justificativa, analista)
        linhas_atualizadas = self.repository.tentar_atualizar_saldo_conta(conta, valor, analista)
        self.repository.registrar_auditoria(
            entidade="conta",
            entidade_id=conta,
            acao="injecao_saldo_teste",
            justificativa=f"{justificativa} | Valor: {valor}",
            analista=analista,
        )
        return {"mensagem": f"Saldo de teste injetado com sucesso. Registro {injecao_id}. Linhas atualizadas: {linhas_atualizadas}."}

    def listar_sla(self, somente_abertas: bool, limite: int) -> dict[str, Any]:
        analises = self.repository.listar_sla(somente_abertas=somente_abertas, limite=limite)
        return {"total": len(analises), "analises": analises}

    def resolver_analise(self, transacao_id: int, status_final: str, justificativa: str, analista: str) -> dict[str, str]:
        linhas = self.repository.resolver_analise_sla(transacao_id, status_final, justificativa, analista)
        self.repository.atualizar_fluxo_transacao(transacao_id, status_transacao=status_final)
        self.repository.registrar_auditoria(
            entidade="transacao",
            entidade_id=transacao_id,
            acao=f"analise_resolvida_{status_final}",
            justificativa=justificativa,
            analista=analista,
        )
        if linhas == 0:
            return {"mensagem": "Nenhuma análise em aberto encontrada, mas a justificativa foi registrada em auditoria."}
        return {"mensagem": f"Análise da transação {transacao_id} concluída como {status_final}."}

    def filtrar_transacoes(
        self,
        cpf: str | None,
        conta: str | None,
        categoria: str | None,
        valor_min: float | None,
        valor_max: float | None,
        limite: int,
    ) -> dict[str, Any]:
        colunas = self.repository.listar_colunas()
        filtros: list[str] = []
        parametros: list[Any] = []
        avisos: list[str] = []

        if cpf:
            if "cpf" in colunas:
                filtros.append("cpf LIKE ?")
                parametros.append(f"%{cpf}%")
            elif "conta" in colunas:
                filtros.append("conta LIKE ?")
                parametros.append(f"%{cpf}%")
                avisos.append(
                    "A base atual não possui coluna CPF; o filtro foi aplicado no campo conta."
                )
            else:
                avisos.append(
                    "A base atual não possui coluna CPF nem conta para aplicar esse filtro."
                )

        if conta:
            if "conta" in colunas:
                filtros.append("conta LIKE ?")
                parametros.append(f"%{conta}%")
            elif "conta_id" in colunas:
                filtros.append("CAST(conta_id AS TEXT) LIKE ?")
                parametros.append(f"%{conta}%")
            else:
                avisos.append("A base atual não possui campo de conta para aplicar esse filtro.")

        if categoria:
            filtros.append("LOWER(categoria) = LOWER(?)")
            parametros.append(categoria)

        if valor_min is not None:
            filtros.append("valor >= ?")
            parametros.append(valor_min)

        if valor_max is not None:
            filtros.append("valor <= ?")
            parametros.append(valor_max)

        total, transacoes = self.repository.filtrar_transacoes(filtros, parametros, limite)

        return {
            "total": total,
            "limite": limite,
            "transacoes": transacoes,
            "avisos": avisos,
        }
