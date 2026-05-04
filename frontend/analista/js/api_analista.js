async function buscarAnomalias() {
    try {
        // Faz a requisição para a sua rota de Anomalias (US05)
        const resposta = await fetch('http://127.0.0.1:8000/anomalies/');
        const anomalias = await resposta.json();
        
        const painel = document.getElementById('painel-alertas');
        painel.innerHTML = ''; 
        
        if (anomalias.length === 0) {
            painel.innerHTML = '<p>✅ Nenhuma anomalia detectada. Sistema seguro.</p>';
            return;
        }

        // Mostra um aviso vermelho para cada fraude encontrada
        anomalias.forEach(anomalia => {
            const divAlerta = document.createElement('div');
            divAlerta.className = 'alerta';
            divAlerta.innerHTML = `
                <strong>ALERTA DE FRAUDE:</strong> 
                Conta: ${anomalia.conta} | Valor Suspeito: € ${anomalia.valor} | Hora: ${anomalia.hora}
            `;
            painel.appendChild(divAlerta);
        });

    } catch (erro) {
        console.error("Erro ao buscar anomalias:", erro);
        alert("Erro! Verifique se a rota /anomalies está no ar.");
    }
}