const API_BASE_URL = 'http://127.0.0.1:8000';

function escaparHTML(valor) {
    return String(valor ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function obterAnalista() {
    let id = localStorage.getItem('analistaId');
    let nome = localStorage.getItem('analistaNome');

    if (!id || !nome) {
        nome = prompt('Informe o nome do analista para auditoria:') || 'Analista não identificado';
        id = prompt('Informe o ID/matrícula do analista:') || 'anonimo';
        localStorage.setItem('analistaId', id);
        localStorage.setItem('analistaNome', nome);
    }

    return { id, nome };
}

function obterCabecalhosAnalista() {
    const analista = obterAnalista();
    return {
        'X-Analista-ID': analista.id,
        'X-Analista-Nome': analista.nome,
    };
}

function trocarAnalista() {
    localStorage.removeItem('analistaId');
    localStorage.removeItem('analistaNome');
    obterAnalista();
    alert('Analista atualizado para os próximos registros de auditoria.');
}

async function buscarAnomalias() {
    try {
        // Faz a requisição para a sua rota de Anomalias (US05)
        const resposta = await fetch(`${API_BASE_URL}/anomalies/`, {
            headers: obterCabecalhosAnalista(),
        });
        const anomalias = await resposta.json();

        const painel = document.getElementById('painel-alertas');
        painel.innerHTML = '<h2>🚨 Transações Suspeitas</h2>';

        if (anomalias.length === 0) {
            painel.innerHTML += '<p>✅ Nenhuma anomalia detectada. Sistema seguro.</p>';
            return;
        }

        // Mostra um aviso vermelho para cada fraude encontrada
        anomalias.forEach(anomalia => {
            const divAlerta = document.createElement('div');
            divAlerta.className = 'alerta';
            divAlerta.innerHTML = `
                <strong>ALERTA DE FRAUDE:</strong>
                Conta: ${escaparHTML(anomalia.conta)} | Valor Suspeito: R$ ${escaparHTML(anomalia.valor)} | Hora: ${escaparHTML(anomalia.hora)}
            `;
            painel.appendChild(divAlerta);
        });

    } catch (erro) {
        console.error('Erro ao buscar anomalias:', erro);
        alert('Erro! Verifique se a rota /anomalies está no ar.');
    }
}

async function buscarLogs() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/registros/logs?limite=20`, {
            headers: obterCabecalhosAnalista(),
        });
        const dados = await resposta.json();
        const painel = document.getElementById('painel-logs');
        painel.innerHTML = '<h2>📋 Histórico de Logs</h2>';

        if (!dados.logs || dados.logs.length === 0) {
            painel.innerHTML += '<p>Nenhum log registrado até o momento.</p>';
            return;
        }

        dados.logs.forEach(log => {
            const divRegistro = document.createElement('div');
            divRegistro.className = 'registro';
            divRegistro.innerHTML = `
                <strong>${escaparHTML(log.metodo)} ${escaparHTML(log.rota)}</strong><br>
                Data/Hora: ${escaparHTML(log.data_hora)}<br>
                Status: ${escaparHTML(log.status_code)} | Tempo: ${escaparHTML(log.tempo_ms)} ms<br>
                IP: ${escaparHTML(log.ip_origem)}
            `;
            painel.appendChild(divRegistro);
        });
    } catch (erro) {
        console.error('Erro ao buscar logs:', erro);
        alert('Erro! Verifique se a rota /registros/logs está no ar.');
    }
}

async function buscarAuditoria() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/registros/auditoria?limite=20`, {
            headers: obterCabecalhosAnalista(),
        });
        const dados = await resposta.json();
        const painel = document.getElementById('painel-auditoria');
        painel.innerHTML = '<h2>🧾 Registro de Auditoria</h2>';

        if (!dados.auditoria || dados.auditoria.length === 0) {
            painel.innerHTML += '<p>Nenhum registro de auditoria encontrado.</p>';
            return;
        }

        dados.auditoria.forEach(registro => {
            const divRegistro = document.createElement('div');
            divRegistro.className = 'registro';
            divRegistro.innerHTML = `
                <strong>${escaparHTML(registro.ator_nome)}</strong> (${escaparHTML(registro.ator_id)})<br>
                Ação: ${escaparHTML(registro.acao)} | Recurso: ${escaparHTML(registro.recurso)}<br>
                Método: ${escaparHTML(registro.metodo)} | Status: ${escaparHTML(registro.status_code)}<br>
                Data/Hora: ${escaparHTML(registro.data_hora)}
            `;
            painel.appendChild(divRegistro);
        });
    } catch (erro) {
        console.error('Erro ao buscar auditoria:', erro);
        alert('Erro! Verifique se a rota /registros/auditoria está no ar.');
    }
}
