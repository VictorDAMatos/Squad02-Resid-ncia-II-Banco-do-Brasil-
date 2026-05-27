export function atualizarTabela(transacoes) {

    const tbody = document.getElementById(
        "historyTableBody"
    );

    tbody.innerHTML = "";

    transacoes.forEach(t => {

        const risco =
            t.risco?.classificacao ||

            t.motor_fraude?.classificacao_risco ||

            "NORMAL";

        let riscoClasse = "risk-low";

        if (risco === "SUSPEITO") {
            riscoClasse = "risk-medium";
        }

        if (
            risco === "CRÍTICO" ||
            risco === "ALTO"
        ) {
            riscoClasse = "risk-high";
        }

        const tr = document.createElement("tr");

        tr.innerHTML = `

            <td>#${t.id}</td>

            <td>${t.conta || "-"}</td>

            <td>
                R$ ${Number(t.valor).toFixed(2)}
            </td>

            <td>${t.cidade || "-"}</td>

            <td class="${riscoClasse}">
                ${risco}
            </td>
        `;

        tbody.appendChild(tr);
    });
}