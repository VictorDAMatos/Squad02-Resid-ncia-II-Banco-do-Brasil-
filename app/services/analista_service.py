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

    def listar_anomalias_detalhadas(self, limite: int = 50) -> list[dict[str, Any]]:
        return self.repository.listar_anomalias_detalhadas(limite=limite)

    def listar_categorias(self) -> dict[str, list[str]]:
        return {"categorias": self.repository.listar_categorias()}

    def listar_contas_bloqueadas(self) -> dict[str, Any]:
        bloqueadas = self.repository.listar_contas_bloqueadas()
        avisos: list[str] = []

        if not bloqueadas:
            colunas = self.repository.listar_colunas()
            if "status_conta" not in colunas:
                avisos.append(
                    "A tabela transactions não possui a coluna status_conta. "
                    "Crie essa coluna ou controle bloqueios em uma tabela própria."
                )

        return {
            "total": len(bloqueadas),
            "bloqueadas": bloqueadas,
            "avisos": avisos,
        }

    def desbloquear_conta(self, conta_id: int) -> dict[str, str]:
        linhas_afetadas = self.repository.desbloquear_conta(conta_id)

        if linhas_afetadas == 0:
            return {
                "mensagem": (
                    f"Nenhuma conta/transação encontrada para o identificador {conta_id} "
                    "ou a base não possui controle de status_conta."
                )
            }

        return {"mensagem": f"Conta {conta_id} desbloqueada com sucesso."}

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
