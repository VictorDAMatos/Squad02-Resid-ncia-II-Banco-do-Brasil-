const API_BASE_URL = (window.location.protocol === 'file:' || !window.location.origin)
    ? 'http://127.0.0.1:8000'
    : window.location.origin;

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

function fmtData(valor) {
    if (!valor) return '—';
    return escaparHTML(valor);
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
        'X-Analista-Token': localStorage.getItem('analistaToken') || 'analista-dev-token',
        'Content-Type': 'application/json',
    };
}

function trocarAnalista() {
    localStorage.removeItem('analistaId');
    localStorage.removeItem('analistaNome');
    obterAnalista();
    alert('Analista atualizado para os próximos registros de auditoria.');
}

async function apiRequest(caminho, opcoes = {}) {
    const headers = { ...obterCabecalhosAnalista(), ...(opcoes.headers || {}) };
    const resposta = await fetch(`${API_BASE_URL}${caminho}`, { ...opcoes, headers });
    const texto = await resposta.text();
    let dados = {};

    if (texto) {
        try { dados = JSON.parse(texto); }
        catch { dados = { mensagem: texto }; }
    }

    if (!resposta.ok) {
        const detalhe = dados.detail || dados.mensagem || `Status HTTP ${resposta.status}`;
        throw new Error(typeof detalhe === 'string' ? detalhe : JSON.stringify(detalhe));
    }

    return dados;
}

function setResultado(id, conteudo, tipo = 'ok') {
    const el = document.getElementById(id);
    if (!el) return;
    const classe = tipo === 'erro' ? 'status-erro' : 'status-ok';
    el.innerHTML = `<div class="${classe}">${tipo === 'erro' ? 'Erro' : 'OK'}</div>${conteudo}`;
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

function pillRisco(risco) {
    const valor = typeof risco === 'string' ? risco : (risco?.intensidade || '—');
    const normalizado = String(valor).toLowerCase();
    const classe = normalizado === 'alto' ? 'pill-danger' : normalizado === 'medio' ? 'pill-warning' : 'pill-info';
    return `<span class="pill ${classe}">${escaparHTML(valor)}</span>`;
}

function contaOuCpf(item) {
    return item.conta || item.cpf || item.conta_id || '—';
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
    if (secao) secao.style.display = '';
    if (!badge || !corpo) return;

    badge.textContent = `${anomalias.length} alertas`;

    if (anomalias.length === 0) {
        corpo.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:24px;color:#2ecc71">✅ Nenhuma anomalia detectada. Sistema seguro.</td></tr>';
        return;
    }

    corpo.innerHTML = anomalias.map(anomalia => {
        const regra = anomalia.regra_alerta || '—';
        const pillClass = regra.includes('Muito') ? 'pill-danger' : regra.includes('Madrugada') ? 'pill-warning' : 'pill-info';
        const suspeito = contaOuCpf(anomalia);
        return `
            <tr>
                <td style="color:var(--muted)">#${escaparHTML(anomalia.id)}</td>
                <td><strong>${escaparHTML(suspeito)}</strong></td>
                <td style="color:#ff6b6b;font-weight:700">${fmt(anomalia.valor)}</td>
                <td>${escaparHTML(anomalia.data)}</td>
                <td>${escaparHTML(anomalia.hora)}</td>
                <td>${escaparHTML(anomalia.categoria)}</td>
                <td>${escaparHTML(anomalia.cidade)}</td>
                <td>${escaparHTML(anomalia.dispositivo)}</td>
                <td><span class="pill ${pillClass}">${escaparHTML(regra)}</span></td>
                <td><div class="row-actions">
                    <button class="primary" onclick="buscarDetalheTransacao(${Number(anomalia.id)})">Detalhe</button>
                    <button class="warning" onclick="processarFluxo(${Number(anomalia.id)})">Fluxo</button>
                    <button class="secondary" onclick="abrirTimeline('${escaparHTML(suspeito)}')">Timeline</button>
                </div></td>
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
        const [dados, anomalias] = await Promise.all([
            apiRequest('/analista/resumo'),
            apiRequest('/analista/anomalias-detalhadas'),
        ]);

        renderKPIs(dados.kpis || {});
        renderGastoMedioDiario([], null);

        if (chartsGrid) chartsGrid.style.display = '';

        criarGrafico('chart-categoria', 'doughnut', (dados.por_categoria || []).map(item => item.categoria || item.nome), (dados.por_categoria || []).map(item => item.volume), { currency: true, legend: true });
        criarGrafico('chart-dispositivo', 'doughnut', (dados.por_dispositivo || []).map(item => item.dispositivo || item.nome), (dados.por_dispositivo || []).map(item => item.qtd), { legend: true });
        criarGrafico('chart-cidade', 'bar', (dados.por_cidade || []).map(item => item.cidade || item.nome), (dados.por_cidade || []).map(item => item.volume), { currency: true, legend: false });
        criarGrafico('chart-tipo', 'bar', (dados.por_tipo || []).map(item => item.tipo_transacao || item.nome), (dados.por_tipo || []).map(item => item.volume), { currency: true, legend: false });
        criarGrafico('chart-hora', 'line', (dados.por_hora || []).map(item => `${item.hora_dia}h`), (dados.por_hora || []).map(item => item.qtd), { fill: true, legend: false });

        renderAnomalias(Array.isArray(anomalias) ? anomalias : []);
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
        const dados = await apiRequest('/analista/categorias');
        const categorias = dados.categorias || [];
        select.innerHTML = '<option value="">Todas</option>' + categorias.map(categoria => (
            `<option value="${escaparHTML(categoria)}">${escaparHTML(categoria)}</option>`
        )).join('');
    } catch (erro) {
        console.error('Erro ao carregar categorias:', erro);
    }
}

function filtrarClienteExtra(transacoes, filtros) {
    return transacoes.filter(t => {
        const alvo = `${t.cpf || ''} ${t.conta || ''} ${t.conta_id || ''}`.toLowerCase();
        const categoria = String(t.categoria || '').toLowerCase();
        const valor = _toNumberValor(t.valor);
        if (filtros.cpf && !alvo.includes(filtros.cpf.toLowerCase())) return false;
        if (filtros.categoria && categoria !== filtros.categoria.toLowerCase()) return false;
        if (filtros.valorMin && valor < Number(filtros.valorMin)) return false;
        if (filtros.valorMax && valor > Number(filtros.valorMax)) return false;
        return true;
    });
}

async function aplicarFiltros() {
    const params = new URLSearchParams();
    const cpf = document.getElementById('filtro-cpf')?.value.trim();
    const categoria = document.getElementById('filtro-categoria')?.value;
    const risco = document.getElementById('filtro-risco')?.value;
    const valorMin = document.getElementById('filtro-valor-min')?.value;
    const valorMax = document.getElementById('filtro-valor-max')?.value;

    const corpo = document.getElementById('tabela-transacoes');
    const badge = document.getElementById('badge-transacoes');
    const aviso = document.getElementById('aviso-filtros');

    if (corpo) corpo.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:20px;color:#7a8fa8">Carregando transações…</td></tr>';
    if (aviso) aviso.innerHTML = '';

    try {
        let dados;
        let transacoes;

        if (risco) {
            params.set('risco', risco);
            params.set('limite', '500');
            dados = await apiRequest(`/analista/transacoes-por-risco?${params.toString()}`);
            transacoes = filtrarClienteExtra(dados.transacoes || [], { cpf, categoria, valorMin, valorMax });
            dados.total = transacoes.length;
            dados.avisos = [
                ...(dados.avisos || []),
                'Filtro por risco usa cálculo do backend e aplica os demais filtros no navegador.'
            ];
        } else {
            if (cpf) params.set('cpf', cpf);
            if (categoria) params.set('categoria', categoria);
            if (valorMin) params.set('valor_min', valorMin);
            if (valorMax) params.set('valor_max', valorMax);
            params.set('limite', '100');
            dados = await apiRequest(`/analista/transacoes-filtradas?${params.toString()}`);
            transacoes = dados.transacoes || [];
        }

        if (badge) badge.textContent = `${fmtN(dados.total || transacoes.length)} registros`;
        if (aviso && dados.avisos?.length) aviso.innerHTML = dados.avisos.map(escaparHTML).join('<br>');

        renderTransacoes(transacoes);
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

    corpo.innerHTML = transacoes.map(transacao => {
        const suspeito = contaOuCpf(transacao);
        return `
            <tr>
                <td style="color:var(--muted)">#${escaparHTML(transacao.id)}</td>
                <td><strong>${escaparHTML(suspeito)}</strong></td>
                <td style="font-weight:700">${fmt(transacao.valor)}</td>
                <td>${escaparHTML(transacao.data)}</td>
                <td>${escaparHTML(transacao.hora)}</td>
                <td>${escaparHTML(transacao.categoria)}</td>
                <td>${escaparHTML(transacao.cidade)}</td>
                <td>${escaparHTML(transacao.tipo_transacao)}</td>
                <td>${escaparHTML(transacao.dispositivo)}</td>
                <td>${transacao.risco ? pillRisco(transacao.risco) : '<span class="muted">—</span>'}</td>
                <td><div class="row-actions">
                    <button class="primary" onclick="buscarDetalheTransacao(${Number(transacao.id)})">Detalhe</button>
                    <button class="warning" onclick="processarFluxo(${Number(transacao.id)})">Fluxo</button>
                    <button class="secondary" onclick="abrirTimeline('${escaparHTML(suspeito)}')">Timeline</button>
                </div></td>
            </tr>
        `;
    }).join('');
}

function _toNumberValor(v) {
    if (typeof v === 'number') return v;
    if (!v) return 0;
    try {
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
        const data = t.data || t.data_transacao || t.data_hora || '';
        const valor = _toNumberValor(t.valor);
        if (!data) return;
        const chave = String(data).slice(0, 10);
        porDia[chave] = (porDia[chave] || 0) + valor;
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
    const risco = document.getElementById('filtro-risco');
    if (risco) risco.value = '';

    const aviso = document.getElementById('aviso-filtros');
    if (aviso) aviso.innerHTML = '';

    aplicarFiltros();
}

async function buscarAnomalias() {
    try {
        const anomalias = await apiRequest('/analista/anomalias-detalhadas');
        renderAnomalias(Array.isArray(anomalias) ? anomalias : []);
    } catch (erro) {
        console.error('Erro ao buscar anomalias:', erro);
        alert(`Erro ao buscar anomalias: ${erro.message}`);
    }
}

async function buscarDetalheTransacao(idParam = null) {
    if (idParam) {
        const botao = document.querySelector('.nav-item[data-section="transacoes"]');
        if (botao && !document.getElementById('page-transacoes')?.classList.contains('active')) navegarPara('transacoes', botao);
    }
    const id = idParam || document.getElementById('detalhe-transacao-id')?.value;
    const output = 'resultado-detalhe-transacao';
    if (!id) return setResultado(output, '<p>Informe o ID da transação.</p>', 'erro');

    const campo = document.getElementById('detalhe-transacao-id');
    if (campo) campo.value = id;

    try {
        const dados = await apiRequest(`/analista/transacoes/${id}`);
        const t = dados.transacao || {};
        const risco = dados.risco || {};
        const perfil = dados.perfil_dispositivo || {};
        const sla = dados.sla;

        setResultado(output, `
            <div class="mini-kpis">
                <div class="mini-kpi"><strong>#${escaparHTML(t.id || id)}</strong><span>Transação</span></div>
                <div class="mini-kpi"><strong>${fmt(t.valor)}</strong><span>Valor</span></div>
                <div class="mini-kpi"><strong>${escaparHTML(risco.intensidade || '—')}</strong><span>Risco</span></div>
                <div class="mini-kpi"><strong>${escaparHTML(t.status_transacao || t.status || '—')}</strong><span>Status</span></div>
            </div>
            <p><strong>Conta/CPF:</strong> ${escaparHTML(contaOuCpf(t))}</p>
            <p><strong>Categoria:</strong> ${escaparHTML(t.categoria)} | <strong>Hora:</strong> ${escaparHTML(t.hora)} | <strong>Dispositivo:</strong> ${escaparHTML(t.dispositivo)}</p>
            <p><strong>Motivos do risco:</strong> ${(risco.motivos || []).map(escaparHTML).join(' | ') || '—'}</p>
            <p><strong>Perfil de dispositivo:</strong> atual ${escaparHTML(perfil.dispositivo_atual || '—')}, mais usado ${escaparHTML(perfil.dispositivo_mais_usado || '—')}, já usado? ${perfil.dispositivo_ja_usado ? 'sim' : 'não'}</p>
            <p><strong>SLA:</strong> ${sla ? `${escaparHTML(sla.status)} — ${escaparHTML(sla.minutos_em_analise)} minutos` : 'sem análise SLA aberta/registrada'}</p>
        `);
    } catch (erro) {
        setResultado(output, `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

async function processarFluxo(id) {
    if (!id) return;
    const botao = document.querySelector('.nav-item[data-section="transacoes"]');
    if (botao && !document.getElementById('page-transacoes')?.classList.contains('active')) navegarPara('transacoes', botao);
    const output = 'resultado-detalhe-transacao';
    try {
        const dados = await apiRequest(`/analista/transacoes/${id}/processar-fluxo`, { method: 'POST' });
        setResultado(output, `
            <p><strong>Transação:</strong> #${escaparHTML(dados.transacao_id)}</p>
            <p><strong>Risco:</strong> ${escaparHTML(dados.risco)}</p>
            <p><strong>Ação automática:</strong> ${escaparHTML(dados.acao_automatica)}</p>
            <p><strong>Mensagem:</strong> ${escaparHTML(dados.mensagem)}</p>
        `);
        await Promise.allSettled([aplicarFiltros(), buscarAnomalias(), buscarContasBloqueadas(), buscarSLA()]);
    } catch (erro) {
        setResultado(output, `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

function processarFluxoPorCampo() {
    const id = document.getElementById('detalhe-transacao-id')?.value;
    if (!id) return setResultado('resultado-detalhe-transacao', '<p>Informe o ID da transação.</p>', 'erro');
    processarFluxo(id);
}

function abrirTimeline(suspeito) {
    const limpo = String(suspeito || '').replaceAll('&amp;', '&');
    const campo = document.getElementById('timeline-suspeito');
    if (campo) campo.value = limpo;
    const botao = document.querySelector('.nav-item[data-section="timeline"]');
    if (botao) navegarPara('timeline', botao);
    buscarTimelineSuspeito(limpo);
}

async function buscarContasBloqueadas() {
    const corpo = document.getElementById('tabela-bloqueios');
    const badge = document.getElementById('badge-bloqueios');
    if (corpo) corpo.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#7a8fa8">Carregando contas bloqueadas…</td></tr>';

    try {
        const dados = await apiRequest('/analista/contas-bloqueadas');
        const bloqueadas = dados.bloqueadas || [];
        if (badge) badge.textContent = `${fmtN(dados.total || bloqueadas.length)} registros`;

        if (!corpo) return;
        if (bloqueadas.length === 0) {
            corpo.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;color:#2ecc71">✅ Nenhuma conta bloqueada no momento.</td></tr>';
            return;
        }

        corpo.innerHTML = bloqueadas.map(item => {
            const conta = contaOuCpf(item);
            return `
                <tr>
                    <td>#${escaparHTML(item.id)}</td>
                    <td><strong>${escaparHTML(conta)}</strong></td>
                    <td>${fmt(item.valor)}</td>
                    <td>${escaparHTML(item.status_conta)}</td>
                    <td>${escaparHTML(item.status_transacao || item.status)}</td>
                    <td>${escaparHTML(item.dispositivo)}</td>
                    <td><div class="row-actions">
                        <button class="success" onclick="prepararDesbloqueio('${escaparHTML(conta)}')">Desbloquear</button>
                        <button class="primary" onclick="buscarDetalheTransacao(${Number(item.id)})">Detalhe</button>
                    </div></td>
                </tr>
            `;
        }).join('');
    } catch (erro) {
        if (corpo) corpo.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:#e74c3c">${escaparHTML(erro.message)}</td></tr>`;
    }
}

function prepararDesbloqueio(conta) {
    const campo = document.getElementById('desbloquear-conta-id');
    if (campo) campo.value = String(conta || '').replaceAll('&amp;', '&');
    const just = document.getElementById('desbloquear-justificativa');
    if (just && !just.value) just.value = 'Cliente confirmou a operação e solicitou desbloqueio da conta.';
}

async function desbloquearContaPorFormulario() {
    const conta = document.getElementById('desbloquear-conta-id')?.value.trim();
    const justificativa = document.getElementById('desbloquear-justificativa')?.value.trim();
    if (!conta) return setResultado('resultado-desbloqueio', '<p>Informe a conta, conta_id ou ID.</p>', 'erro');
    if (!justificativa || justificativa.length < 10) return setResultado('resultado-desbloqueio', '<p>A justificativa precisa ter pelo menos 10 caracteres.</p>', 'erro');
    await desbloquearConta(conta, justificativa);
}

async function desbloquearConta(conta, justificativa) {
    try {
        const analista = obterAnalista();
        const dados = await apiRequest(`/analista/desbloquear/${encodeURIComponent(conta)}`, {
            method: 'POST',
            body: JSON.stringify({ justificativa, analista: analista.nome }),
        });
        setResultado('resultado-desbloqueio', `<p>${escaparHTML(dados.mensagem)}</p>`);
        await buscarContasBloqueadas();
    } catch (erro) {
        setResultado('resultado-desbloqueio', `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

async function buscarTimelineSuspeito(suspeitoParam = null) {
    const suspeito = suspeitoParam || document.getElementById('timeline-suspeito')?.value.trim();
    if (!suspeito) return setResultado('resultado-timeline', '<p>Informe CPF, conta ou conta_id do suspeito.</p>', 'erro');

    try {
        const dados = await apiRequest(`/analista/suspeitos/${encodeURIComponent(suspeito)}/timeline`);
        const perfil = dados.perfil || {};
        const transacoes = dados.transacoes || [];
        const notificacoes = dados.notificacoes || [];
        const auditoria = dados.auditoria || [];
        const dispositivos = dados.dispositivos || [];

        setResultado('resultado-timeline', `
            <div class="mini-kpis">
                <div class="mini-kpi"><strong>${fmtN(perfil.total_transacoes || 0)}</strong><span>Transações</span></div>
                <div class="mini-kpi"><strong>${fmt(perfil.volume_total || 0)}</strong><span>Volume total</span></div>
                <div class="mini-kpi"><strong>${fmtN(perfil.qtd_risco_alto || 0)}</strong><span>Risco alto</span></div>
                <div class="mini-kpi"><strong>${fmtN(perfil.qtd_risco_medio || 0)}</strong><span>Risco médio</span></div>
            </div>
            <p><strong>Dispositivos:</strong> ${dispositivos.map(d => `${escaparHTML(d.dispositivo)} (${fmtN(d.qtd)})`).join(' | ') || '—'}</p>
            <h3>Últimas transações</h3>
            <ul>${transacoes.slice(0, 10).map(t => `<li>#${escaparHTML(t.id)} — ${fmt(t.valor)} — ${escaparHTML(t.categoria)} — ${escaparHTML(t.hora)} — ${escaparHTML(t.dispositivo)}</li>`).join('') || '<li>Nenhuma transação encontrada.</li>'}</ul>
            <h3>Notificações</h3>
            <ul>${notificacoes.slice(0, 10).map(n => `<li>${fmtData(n.criado_em)} — ${escaparHTML(n.canal)} — ${escaparHTML(n.mensagem)}</li>`).join('') || '<li>Nenhuma notificação registrada.</li>'}</ul>
            <h3>Auditoria</h3>
            <ul>${auditoria.slice(0, 10).map(a => `<li>${fmtData(a.criado_em)} — ${escaparHTML(a.acao)} — ${escaparHTML(a.justificativa)}</li>`).join('') || '<li>Nenhuma auditoria específica encontrada.</li>'}</ul>
        `);
    } catch (erro) {
        setResultado('resultado-timeline', `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

async function registrarNotificacao() {
    const suspeito = document.getElementById('notif-suspeito')?.value.trim();
    const canal = document.getElementById('notif-canal')?.value || 'sistema';
    const transacaoIdRaw = document.getElementById('notif-transacao-id')?.value;
    const mensagem = document.getElementById('notif-mensagem')?.value.trim();
    if (!suspeito) return setResultado('resultado-notificacao', '<p>Informe o suspeito.</p>', 'erro');
    if (!mensagem || mensagem.length < 3) return setResultado('resultado-notificacao', '<p>Informe uma mensagem válida.</p>', 'erro');

    try {
        const analista = obterAnalista();
        const payload = {
            suspeito,
            mensagem,
            canal,
            transacao_id: transacaoIdRaw ? Number(transacaoIdRaw) : null,
            analista: analista.nome,
        };
        const dados = await apiRequest('/analista/notificacoes', { method: 'POST', body: JSON.stringify(payload) });
        setResultado('resultado-notificacao', `<p>${escaparHTML(dados.mensagem)}</p>`);
        await buscarNotificacoes();
    } catch (erro) {
        setResultado('resultado-notificacao', `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

async function buscarNotificacoes() {
    const corpo = document.getElementById('tabela-notificacoes');
    const badge = document.getElementById('badge-notificacoes');
    if (corpo) corpo.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#7a8fa8">Carregando notificações…</td></tr>';

    try {
        const dados = await apiRequest('/analista/notificacoes?limite=100');
        const notificacoes = dados.notificacoes || [];
        if (badge) badge.textContent = `${fmtN(dados.total || notificacoes.length)} registros`;

        if (!corpo) return;
        if (notificacoes.length === 0) {
            corpo.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;color:#7a8fa8">Nenhuma notificação registrada.</td></tr>';
            return;
        }

        corpo.innerHTML = notificacoes.map(n => `
            <tr>
                <td>#${escaparHTML(n.id)}</td>
                <td><strong>${escaparHTML(n.suspeito)}</strong></td>
                <td>${escaparHTML(n.transacao_id || '—')}</td>
                <td>${escaparHTML(n.canal)}</td>
                <td>${escaparHTML(n.mensagem)}</td>
                <td>${escaparHTML(n.analista)}</td>
                <td>${fmtData(n.criado_em)}</td>
            </tr>
        `).join('');
    } catch (erro) {
        if (corpo) corpo.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:#e74c3c">${escaparHTML(erro.message)}</td></tr>`;
    }
}

async function injetarSaldo() {
    const conta = document.getElementById('saldo-conta')?.value.trim();
    const valor = Number(document.getElementById('saldo-valor')?.value || 0);
    const justificativa = document.getElementById('saldo-justificativa')?.value.trim();
    if (!conta) return setResultado('resultado-saldo', '<p>Informe a conta.</p>', 'erro');
    if (!valor || valor <= 0) return setResultado('resultado-saldo', '<p>Informe um valor maior que zero.</p>', 'erro');
    if (!justificativa || justificativa.length < 10) return setResultado('resultado-saldo', '<p>A justificativa precisa ter pelo menos 10 caracteres.</p>', 'erro');

    try {
        const analista = obterAnalista();
        const dados = await apiRequest('/analista/injetar-saldo', {
            method: 'POST',
            body: JSON.stringify({ conta, valor, justificativa, analista: analista.nome }),
        });
        setResultado('resultado-saldo', `<p>${escaparHTML(dados.mensagem)}</p>`);
        await aplicarFiltros();
    } catch (erro) {
        setResultado('resultado-saldo', `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

async function buscarSLA() {
    const somente = document.getElementById('sla-somente-abertas')?.value ?? 'true';
    const corpo = document.getElementById('tabela-sla');
    const badge = document.getElementById('badge-sla');
    if (corpo) corpo.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#7a8fa8">Carregando SLA…</td></tr>';

    try {
        const dados = await apiRequest(`/analista/sla?somente_abertas=${somente}&limite=100`);
        const analises = dados.analises || [];
        if (badge) badge.textContent = `${fmtN(dados.total || analises.length)} registros`;
        if (!corpo) return;

        if (analises.length === 0) {
            corpo.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:24px;color:#7a8fa8">Nenhuma análise SLA encontrada.</td></tr>';
            return;
        }

        corpo.innerHTML = analises.map(a => `
            <tr>
                <td>#${escaparHTML(a.id)}</td>
                <td><strong>#${escaparHTML(a.transacao_id)}</strong></td>
                <td>${escaparHTML(a.status)}</td>
                <td>${pillRisco(a.risco)}</td>
                <td>${fmtData(a.iniciado_em)}</td>
                <td>${fmtData(a.resolvido_em)}</td>
                <td>${escaparHTML(a.minutos_em_analise ?? '—')}</td>
                <td>${escaparHTML(a.analista || '—')}</td>
                <td><div class="row-actions">
                    <button class="success" onclick="prepararResolverSLA(${Number(a.transacao_id)})">Resolver</button>
                    <button class="primary" onclick="buscarDetalheTransacao(${Number(a.transacao_id)})">Detalhe</button>
                </div></td>
            </tr>
        `).join('');
    } catch (erro) {
        if (corpo) corpo.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:20px;color:#e74c3c">${escaparHTML(erro.message)}</td></tr>`;
    }
}

function prepararResolverSLA(transacaoId) {
    const campo = document.getElementById('sla-transacao-id');
    if (campo) campo.value = transacaoId;
    const just = document.getElementById('sla-justificativa');
    if (just && !just.value) just.value = 'Cliente confirmou a operação e a análise foi concluída pelo analista.';
}

async function resolverSLA(idParam = null) {
    const transacaoId = idParam || document.getElementById('sla-transacao-id')?.value;
    const statusFinal = document.getElementById('sla-status-final')?.value || 'aprovada';
    const justificativa = document.getElementById('sla-justificativa')?.value.trim();
    if (!transacaoId) return setResultado('resultado-sla', '<p>Informe o ID da transação.</p>', 'erro');
    if (!justificativa || justificativa.length < 10) return setResultado('resultado-sla', '<p>A justificativa precisa ter pelo menos 10 caracteres.</p>', 'erro');

    try {
        const analista = obterAnalista();
        const dados = await apiRequest(`/analista/sla/${transacaoId}/resolver`, {
            method: 'POST',
            body: JSON.stringify({ status_final: statusFinal, justificativa, analista: analista.nome }),
        });
        setResultado('resultado-sla', `<p>${escaparHTML(dados.mensagem)}</p>`);
        await buscarSLA();
    } catch (erro) {
        setResultado('resultado-sla', `<p>${escaparHTML(erro.message)}</p>`, 'erro');
    }
}

async function buscarLogs() {
    try {
        const dados = await apiRequest('/registros/logs?limite=20');
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
    } catch (erro) {
        console.error('Erro ao buscar logs:', erro);
        alert(`Erro ao buscar logs: ${erro.message}`);
    }
}

async function buscarAuditoria() {
    try {
        const dados = await apiRequest('/registros/auditoria?limite=20');
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
    } catch (erro) {
        console.error('Erro ao buscar auditoria:', erro);
        alert(`Erro ao buscar auditoria: ${erro.message}`);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    carregarDados();
    carregarCategorias();
    aplicarFiltros();
});
