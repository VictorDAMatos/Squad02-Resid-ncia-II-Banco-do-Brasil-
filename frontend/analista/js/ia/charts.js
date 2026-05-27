let chart;

export function atualizarGraficos(transacoes) {

    const ctx =
        document.getElementById("riskChart");

    if (!ctx) return;

    const labels = transacoes.map(
        t => `#${t.id}`
    );

    const valores = transacoes.map(t => {

        const risco =
            t.risco?.classificacao ||

            t.motor_fraude?.classificacao_risco ||

            "NORMAL";

        if (
            risco === "CRÍTICO" ||
            risco === "ALTO"
        ) {
            return 95;
        }

        if (risco === "SUSPEITO") {
            return 60;
        }

        return 15;
    });

    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {

        type: "line",

        data: {

            labels,

            datasets: [

                {
                    label: "Ameaça Detectada",

                    data: valores,

                    borderColor: "#00ffff",

                    backgroundColor:
                        "rgba(0,255,255,0.15)",

                    fill: true,

                    borderWidth: 3,

                    tension: 0.45,

                    pointRadius: 5
                }
            ]
        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    labels: {
                        color: "#ffffff"
                    }
                }
            },

            scales: {

                y: {

                    min: 0,

                    max: 100,

                    ticks: {

                        color: "#cccccc"
                    },

                    grid: {

                        color:
                            "rgba(255,255,255,0.05)"
                    }
                },

                x: {

                    ticks: {

                        color: "#cccccc"
                    },

                    grid: {

                        color:
                            "rgba(255,255,255,0.05)"
                    }
                }
            }
        }
    });
}