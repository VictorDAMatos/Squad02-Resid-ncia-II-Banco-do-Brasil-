import {
    getDashboardIA,
    getTransacoes
}
from "./apiIA.js";

import {
    atualizarTabela
}
from "./tableIA.js";

import {
    atualizarGraficos
}
from "./chartsIA.js";

async function carregarDashboard() {

    try {

        const dashboard =
            await getDashboardIA();

        const transacoes =
            await getTransacoes();

        document.getElementById(
            "totalTransacoes"
        ).innerText =
            dashboard.total_transacoes || 0;

        document.getElementById(
            "suspeitas"
        ).innerText =
            dashboard.suspeitas || 0;

        document.getElementById(
            "bloqueadas"
        ).innerText =
            dashboard.bloqueadas || 0;

        document.getElementById(
            "taxaFraude"
        ).innerText =
            `${dashboard.taxa_fraude || 0}%`;

        atualizarTabela(
            transacoes
        );

        atualizarGraficos(
            transacoes
        );

    }

    catch(error) {

        console.error(
            "Erro IA:",
            error
        );
    }
}

carregarDashboard();