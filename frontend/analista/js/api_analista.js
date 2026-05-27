const API_BASE_URL = 'http://127.0.0.1:8000';
const PALETTE = ['#F9C300', '#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#e67e22', '#1abc9c'];
let chartsInstanciados = {};

function escaparHTML(valor) {
    return String(valor ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function fmt(valor) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor || 0));
}

function fmtN(valor) {
    return new Intl.NumberFormat('pt-BR').format(Math.round(Number(valor || 0)));
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

function destroyChart(id) {
    if (chartsInstanciados[id]) {
        chartsInstanciados[id].destroy();
        delete chartsInstanciados[id];
    }
}

function criarGrafico(id, tipo, labels, dados, opts = {}) {
    if (typeof Chart === 'undefined') return;

    const elemento = document.getElementById(id);
    if (!elemento) return;

    destroyChart(id);
    const ctx = elemento.getContext('2d');

    chartsInstanciados[id] = new Chart(ctx, {
        type: tipo,
        data: {
            labels,
            datasets: [{
                data: dados,
                backgroundColor: opts.solid ? PALETTE[0] : PALETTE.slice(0, Math.max(labels.length, 1)),
                borderColor: opts.solid ? PALETTE[0] : PALETTE.slice(0, Math.max(labels.length, 1)),
                borderWidth: tipo === 'bar' ? 0 : 2,
                borderRadius: tipo === 'bar' ? 6 : 0,
                fill: opts.fill ?? false,
                tension: 0.4,
                pointBackgroundColor: PALETTE[0],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: opts.legend ?? (tipo === 'doughnut' || tipo === 'pie'),
                    labels: { color: '#7a8fa8', font: { size: 11 }, boxWidth: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => opts.currency
                            ? ` ${fmt(ctx.parsed.y ?? ctx.parsed)}`
                            : ` ${fmtN(ctx.parsed.y ?? ctx.parsed)}`
                    }
                }
            },
            scales: tipo === 'bar' || tipo === 'line' ? {
                x: { ticks: { color: '#7a8fa8', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,.05)' } },
                y: { ticks: { color: '#7a8fa8', font: { size: 11 }, callback: v => opts.currency ? fmt(v) : fmtN(v) }, grid: { color: 'rgba(255,255,255,.05)' } }
            } : {}
        }
    });
}

function renderKPIs(kpis) {
    const grid = document.getElementById('kpi-grid');
    if (!grid) return;

    const cards = [
        { label: 'Total de Transações', value: fmtN(kpis.total), sub: 'registros no banco', icon: '📋', accent: '#3498db' },
        { label: 'Volume Movimentado', value: fmt(kpis.volume), sub: 'soma geral', icon: '💰', accent: '#F9C300' },
        { label: 'Ticket Médio', value: fmt(kpis.media), sub: 'por transação', icon: '📊', accent: '#2ecc71' },
        { label: 'Maior Transação', value: fmt(kpis.maior), sub: 'valor máximo', icon: '📈', accent: '#9b59b6' },
        { label: 'Alertas de Fraude', value: fmtN(kpis.total_anomalias), sub: 'transações suspeitas', icon: '🚨', accent: '#e74c3c' },
    ];

    grid.innerHTML = cards.map(card => `
        <div class="kpi-card" style="--accent:${card.accent}">
            <div class="icon">${card.icon}</div>
            <div class="label">${card.label}</div>
            <div class="value">${card.value}</div>
            <div class="sub">${card.sub}</div>
        </div>
    `).join('');
}

function renderAnomalias(anomalias) {
    const secao = document.getElementById('alertas-section');
    const badge = document.getElementById('badge-anomalias');
    const corpo = document.getElementById('tabela-anomalias');
    if (!secao || !badge || !corpo) return;

    secao.style.display = '';
    badge.textContent = `${anomalias.length} alertas`;

    if (anomalias.length === 0) {
        corpo.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:24px;color:#2ecc71">✅ Nenhuma anomalia detectada. Sistema seguro.</td></tr>';
        return;
    }

    corpo.innerHTML = anomalias.map(anomalia => {
        const regra = anomalia.regra_alerta || '—';
        const pillClass = regra.includes('Muito') ? 'pill-danger' : regra.includes('Madrugada') ? 'pill-warning' : 'pill-info';
        return `
            <tr>
                <td style="color:var(--muted)">#${escaparHTML(anomalia.id)}</td>
                <td><strong>${escaparHTML(anomalia.conta)}</strong></td>
                <td style="color:#ff6b6b;font-weight:700">${fmt(anomalia.valor)}</td>
                <td>${escaparHTML(anomalia.data)}</td>
                <td>${escaparHTML(anomalia.hora)}</td>
                <td>${escaparHTML(anomalia.categoria)}</td>
                <td>${escaparHTML(anomalia.cidade)}</td>
                <td>${escaparHTML(anomalia.dispositivo)}</td>
                <td><span class="pill ${pillClass}">${escaparHTML(regra)}</span></td>
            </tr>
        `;
    }).join('');
}

async function carregarDados() {
    const errorArea = document.getElementById('error-area');
    const chartsGrid = document.getElementById('charts-grid');
    const alertasSection = document.getElementById('alertas-section');
    const kpiGrid = document.getElementById('kpi-grid');

    if (errorArea) errorArea.innerHTML = '';
    if (chartsGrid) chartsGrid.style.display = 'none';
    if (alertasSection) alertasSection.style.display = 'none';
    if (kpiGrid) kpiGrid.innerHTML = '<div class="loading-overlay" style="grid-column:1/-1"><div class="spinner"></div><span>Carregando painel…</span></div>';

    try {
        const cabecalhos = obterCabecalhosAnalista();
        const [resumoRes, anomaliasRes] = await Promise.all([
            fetch(`${API_BASE_URL}/analista/resumo`, { headers: cabecalhos }),
            fetch(`${API_BASE_URL}/analista/anomalias-detalhadas`, { headers: cabecalhos }),
        ]);

        if (!resumoRes.ok) throw new Error(`Endpoint /analista/resumo retornou ${resumoRes.status}`);

        const dados = await resumoRes.json();
        const anomalias = anomaliasRes.ok ? await anomaliasRes.json() : [];

        renderKPIs(dados.kpis || {});

        // adiciona placeholder para o cartão de gasto médio diário (será preenchido ao aplicar filtros)
        renderGastoMedioDiario([], null);

        if (chartsGrid) chartsGrid.style.display = '';

        criarGrafico(
            'chart-categoria',
            'doughnut',
            (dados.por_categoria || []).map(item => item.categoria),
            (dados.por_categoria || []).map(item => item.volume),
            { currency: true, legend: true }
        );

        criarGrafico(
            'chart-dispositivo',
            'doughnut',
            (dados.por_dispositivo || []).map(item => item.dispositivo),
            (dados.por_dispositivo || []).map(item => item.qtd),
            { legend: true }
        );

        criarGrafico(
            'chart-cidade',
            'bar',
            (dados.por_cidade || []).map(item => item.cidade),
            (dados.por_cidade || []).map(item => item.volume),
            { currency: true, legend: false }
        );

        criarGrafico(
            'chart-tipo',
            'bar',
            (dados.por_tipo || []).map(item => item.tipo_transacao),
            (dados.por_tipo || []).map(item => item.volume),
            { currency: true, legend: false }
        );

        criarGrafico(
            'chart-hora',
            'line',
            (dados.por_hora || []).map(item => `${item.hora_dia}h`),
            (dados.por_hora || []).map(item => item.qtd),
            { fill: true, legend: false }
        );

        renderAnomalias(anomalias);
    } catch (erro) {
        if (kpiGrid) kpiGrid.innerHTML = '';
        if (errorArea) {
            errorArea.innerHTML = `
                <div class="error-msg">
                    <strong>⚠️ Erro ao conectar na API</strong><br/>
                    <small>${escaparHTML(erro.message)}</small><br/><br/>
                    Certifique-se de que a API está rodando em <code>${API_BASE_URL}</code>
                </div>`;
        }
        console.error(erro);
    }
}

async function carregarCategorias() {
    const select = document.getElementById('filtro-categoria');
    if (!select) return;

    try {
        const resposta = await fetch(`${API_BASE_URL}/analista/categorias`, {
            headers: obterCabecalhosAnalista(),
        });
        if (!resposta.ok) return;

        const dados = await resposta.json();
        const categorias = dados.categorias || [];
        select.innerHTML = '<option value="">Todas</option>' + categorias.map(categoria => (
            `<option value="${escaparHTML(categoria)}">${escaparHTML(categoria)}</option>`
        )).join('');
    } catch (erro) {
        console.error('Erro ao carregar categorias:', erro);
    }
}

async function aplicarFiltros() {
    const params = new URLSearchParams();
    const cpf = document.getElementById('filtro-cpf')?.value.trim();
    const categoria = document.getElementById('filtro-categoria')?.value;
    const valorMin = document.getElementById('filtro-valor-min')?.value;
    const valorMax = document.getElementById('filtro-valor-max')?.value;

    if (cpf) params.set('cpf', cpf);
    if (categoria) params.set('categoria', categoria);
    if (valorMin) params.set('valor_min', valorMin);
    if (valorMax) params.set('valor_max', valorMax);
    params.set('limite', '100');

    const corpo = document.getElementById('tabela-transacoes');
    const badge = document.getElementById('badge-transacoes');
    const aviso = document.getElementById('aviso-filtros');

    if (corpo) corpo.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:20px;color:#7a8fa8">Carregando transações filtradas…</td></tr>';
    if (aviso) aviso.innerHTML = '';

    try {
        const resposta = await fetch(`${API_BASE_URL}/analista/transacoes-filtradas?${params.toString()}`, {
            headers: obterCabecalhosAnalista(),
        });

        if (!resposta.ok) throw new Error(`Endpoint /analista/transacoes-filtradas retornou ${resposta.status}`);

        const dados = await resposta.json();
        const transacoes = dados.transacoes || [];

        if (badge) badge.textContent = `${fmtN(dados.total || transacoes.length)} registros`;
        if (aviso && dados.avisos?.length) aviso.innerHTML = dados.avisos.map(escaparHTML).join('<br>');

        renderTransacoes(transacoes);
        // atualiza o cartão de Gasto Médio Diário com base nas transações filtradas
        renderGastoMedioDiario(transacoes, cpf);
    } catch (erro) {
        if (corpo) corpo.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:20px;color:#e74c3c">Erro ao aplicar filtros: ${escaparHTML(erro.message)}</td></tr>`;
        console.error('Erro ao aplicar filtros:', erro);
    }
}

function renderTransacoes(transacoes) {
    const corpo = document.getElementById('tabela-transacoes');
    if (!corpo) return;

    if (transacoes.length === 0) {
        corpo.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:24px;color:#7a8fa8">Nenhuma transação encontrada para os filtros selecionados.</td></tr>';
        return;
    }

    corpo.innerHTML = transacoes.map(transacao => `
        <tr>
            <td style="color:var(--muted)">#${escaparHTML(transacao.id)}</td>
            <td><strong>${escaparHTML(transacao.cpf || transacao.conta || '—')}</strong></td>
            <td style="font-weight:700">${fmt(transacao.valor)}</td>
            <td>${escaparHTML(transacao.data)}</td>
            <td>${escaparHTML(transacao.hora)}</td>
            <td>${escaparHTML(transacao.categoria)}</td>
            <td>${escaparHTML(transacao.cidade)}</td>
            <td>${escaparHTML(transacao.tipo_transacao)}</td>
            <td>${escaparHTML(transacao.dispositivo)}</td>
            <td><span class="pill ${transacao.classificacao_risco === 'vermelho' ? 'pill-danger' : transacao.classificacao_risco === 'amarelo' ? 'pill-warning' : 'pill-info'}">${escaparHTML(transacao.classificacao_risco || 'verde')}</span></td>
            <td>${escaparHTML(transacao.status_transacao || 'aprovada')} / ${escaparHTML(transacao.status_conta || 'Ativa')}</td>
        </tr>
    `).join('');
}

function _toNumberValor(v) {
    if (typeof v === 'number') return v;
    if (!v) return 0;
    try {
        // aceita formatos como 1.234,56 ou 1234.56
        const s = String(v).trim().replace(/\./g, '').replace(/,/, '.');
        return Number(s) || 0;
    } catch (e) {
        return 0;
    }
}

function calcularGastoMedioDiario(transacoes) {
    if (!transacoes || transacoes.length === 0) return 0;
    const porDia = {};
    let total = 0;

    transacoes.forEach(t => {
        const data = t.data || t.data_transacao || '';
        const valor = _toNumberValor(t.valor);
        if (!data) return;
        porDia[data] = (porDia[data] || 0) + valor;
        total += valor;
    });

    const dias = Object.keys(porDia).length || 1;
    return total / dias;
}

function renderGastoMedioDiario(transacoes, cpf) {
    const grid = document.getElementById('kpi-grid');
    if (!grid) return;

    const id = 'kpi-gasto-medio-diario';
    const label = 'Gasto Médio Diário';
    const sub = cpf ? `cliente ${escaparHTML(cpf)}` : 'filtre por CPF/Conta';

    let value = '—';
    if (cpf && transacoes && transacoes.length) {
        const avg = calcularGastoMedioDiario(transacoes);
        value = fmt(avg);
    }

    const cardHtml = `
        <div class="kpi-card" id="${id}" style="--accent:var(--bb-yellow)">
            <div class="icon">🧾</div>
            <div class="label">${label}</div>
            <div class="value">${value}</div>
            <div class="sub">${sub}</div>
        </div>
    `;

    const existing = document.getElementById(id);
    if (existing) existing.outerHTML = cardHtml;
    else grid.insertAdjacentHTML('beforeend', cardHtml);
}

function limparFiltros() {
    const campos = ['filtro-cpf', 'filtro-valor-min', 'filtro-valor-max'];
    campos.forEach(id => {
        const campo = document.getElementById(id);
        if (campo) campo.value = '';
    });

    const categoria = document.getElementById('filtro-categoria');
    if (categoria) categoria.value = '';

    const aviso = document.getElementById('aviso-filtros');
    if (aviso) aviso.innerHTML = '';

    aplicarFiltros();
}

async function buscarAnomalias() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/analista/anomalias-detalhadas`, {
            headers: obterCabecalhosAnalista(),
        });
        if (!resposta.ok) throw new Error(`Status ${resposta.status}`);
        const anomalias = await resposta.json();
        renderAnomalias(anomalias);
        document.getElementById('alertas-section')?.scrollIntoView({ behavior: 'smooth' });
    } catch (erro) {
        console.error('Erro ao buscar anomalias:', erro);
        alert('Erro! Verifique se a rota /analista/anomalias-detalhadas está no ar.');
    }
}

async function buscarLogs() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/registros/logs?limite=20`, {
            headers: obterCabecalhosAnalista(),
        });
        const dados = await resposta.json();
        const painel = document.getElementById('painel-logs');
        if (!painel) return;

        painel.classList.remove('hidden');
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
        painel.scrollIntoView({ behavior: 'smooth' });
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
        if (!painel) return;

        painel.classList.remove('hidden');
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
        painel.scrollIntoView({ behavior: 'smooth' });
    } catch (erro) {
        console.error('Erro ao buscar auditoria:', erro);
        alert('Erro! Verifique se a rota /registros/auditoria está no ar.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    carregarDados();
    carregarCategorias();
    aplicarFiltros();
});
