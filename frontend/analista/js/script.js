const API_BASE_URL = 'http://127.0.0.1:8000';
const USAR_BACKEND_AUTOMATICAMENTE = true;

const estado = {
  paginaAtual: 'view-dashboard',
  graficos: {},
  filaRisco: [
    {
      id: 'TX-992A',
      alvo: 'Victor Daniel',
      conta: '67559-9',
      canal: 'Pix Mobile',
      valor: 15400.50,
      score: 94,
      risco: 'Alto',
      status: 'Pendente',
      cidade: 'Aracaju-SE',
      dispositivo: 'iPhone 14 Pro',
      horario: '10:04'
    },
    {
      id: 'TX-104B',
      alvo: 'Julia Mendes',
      conta: '58392-1',
      canal: 'Internet Banking',
      valor: 450.00,
      score: 18,
      risco: 'Baixo',
      status: 'Aprovada',
      cidade: 'Salvador-BA',
      dispositivo: 'Notebook Dell',
      horario: '10:15'
    },
    {
      id: 'TX-551C',
      alvo: 'Marcos Silva',
      conta: '4412-X',
      canal: 'TED',
      valor: 8900.20,
      score: 72,
      risco: 'Alto',
      status: 'Em análise',
      cidade: 'Maceió-AL',
      dispositivo: 'Android VPN',
      horario: '10:25'
    },
    {
      id: 'TX-774D',
      alvo: 'Ana Beatriz Lima',
      conta: '90231-4',
      canal: 'Cartão Virtual',
      valor: 1200.00,
      score: 49,
      risco: 'Médio',
      status: 'Em análise',
      cidade: 'Recife-PE',
      dispositivo: 'Chrome Windows',
      horario: '11:02'
    },
    {
      id: 'TX-882E',
      alvo: 'Carlos Eduardo',
      conta: '11802-0',
      canal: 'Saque Digital',
      valor: 380.00,
      score: 26,
      risco: 'Baixo',
      status: 'Aprovada',
      cidade: 'Aracaju-SE',
      dispositivo: 'Caixa 24h',
      horario: '11:14'
    }
  ],
  dispositivos: [
    {
      conta: '67559-9',
      hardware: 'iPhone 14 Pro · IP 192.168.0.10',
      localizacao: 'Aracaju-SE',
      status: 'Alerta Crítico'
    },
    {
      conta: '4412-X',
      hardware: 'Poco X5 · VPN externa',
      localizacao: 'Rota internacional',
      status: 'Alerta Crítico'
    },
    {
      conta: '58392-1',
      hardware: 'Notebook Dell · IP residencial',
      localizacao: 'Salvador-BA',
      status: 'Confiável'
    },
    {
      conta: '90231-4',
      hardware: 'Chrome Windows · IP novo',
      localizacao: 'Recife-PE',
      status: 'Observação'
    }
  ],
  sla: [
    {
      ref: 'CASO-01',
      analista: 'Victor Daniel',
      tempo: '4m 12s',
      status: 'Dentro do prazo'
    },
    {
      ref: 'CASO-02',
      analista: 'Julia Mendes',
      tempo: '14m 50s',
      status: 'Atenção'
    },
    {
      ref: 'CASO-03',
      analista: 'Marcos Silva',
      tempo: '18m 08s',
      status: 'Atrasado'
    },
    {
      ref: 'CASO-04',
      analista: 'Ana Beatriz',
      tempo: '2m 44s',
      status: 'Dentro do prazo'
    }
  ],
  bloqueios: [
    {
      conta: '67559-9',
      titular: 'Victor Daniel',
      motivo: 'Pix de alto valor em dispositivo recém-detectado',
      origem: 'AICore',
      dataHora: '26/05/2026 10:08'
    },
    {
      conta: '4412-X',
      titular: 'Marcos Silva',
      motivo: 'IP mascarado com rota internacional',
      origem: 'Regra automática',
      dataHora: '26/05/2026 10:31'
    }
  ],
  iaAlvos: [
    {
      alvo: 'Victor Daniel · CPF final 88',
      score: '94.2%',
      acao: 'Bloqueio preventivo',
      confianca: 'Alta'
    },
    {
      alvo: 'Marcos Silva · CPF final 12',
      score: '81.5%',
      acao: 'Análise manual',
      confianca: 'Alta'
    },
    {
      alvo: 'Ana Beatriz · CPF final 04',
      score: '68.5%',
      acao: 'Monitorar por 24h',
      confianca: 'Média'
    },
    {
      alvo: 'Julia Mendes · CPF final 51',
      score: '19.8%',
      acao: 'Aprovar fluxo',
      confianca: 'Baixa'
    }
  ],
  logsIa: [
    {
      titulo: 'Feature: dispositivo_novo',
      texto: 'Peso elevado na inferência por primeiro acesso no canal móvel para conta de alto limite.'
    },
    {
      titulo: 'Feature: valor_atípico',
      texto: 'Valor acima do percentil 95 do histórico recente da conta monitorada.'
    },
    {
      titulo: 'Feature: localização_incomum',
      texto: 'Distância comportamental alta em relação ao padrão de cidade e IP residencial.'
    },
    {
      titulo: 'Cluster: C-03',
      texto: 'Grupo associado a operações de urgência, Pix alto e mudança súbita de dispositivo.'
    },
    {
      titulo: 'Regra híbrida',
      texto: 'Modelo combinou score neural com regra determinística para recomendação de bloqueio.'
    },
    {
      titulo: 'Auditoria explicável',
      texto: 'Registro pronto para envio ao log de auditoria do back-end quando a integração estiver ativa.'
    }
  ],
  justificativas: [
    {
      horario: '10:08',
      analista: 'Victor Daniel',
      acao: 'Bloqueio preventivo',
      justificativa: 'Transação TX-992A retida por alto valor e dispositivo novo.'
    },
    {
      horario: '10:31',
      analista: 'AICore',
      acao: 'Escalonamento',
      justificativa: 'Conta 4412-X enviada para análise manual por rota VPN.'
    }
  ]
};

function escaparHTML(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatarMoeda(valor) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(Number(valor || 0));
}

function formatarNumero(valor) {
  return new Intl.NumberFormat('pt-BR').format(Number(valor || 0));
}

function obterCorTextoGrafico() {
  return document.body.classList.contains('dark-theme') ? '#9baeca' : '#64748b';
}

function obterCorGradeGrafico() {
  return document.body.classList.contains('dark-theme') ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.08)';
}

function destruirGrafico(chave) {
  if (estado.graficos[chave]) {
    estado.graficos[chave].destroy();
    delete estado.graficos[chave];
  }
}

function destruirTodosGraficos() {
  Object.keys(estado.graficos).forEach(destruirGrafico);
}

function criarGrafico(chave, canvasId, configuracao) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js não foi carregado. Verifique a conexão com a CDN.');
    return;
  }

  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destruirGrafico(chave);
  estado.graficos[chave] = new Chart(canvas.getContext('2d'), configuracao);
}

function montarOpcoesGrafico(tipo, extras = {}) {
  const corTexto = obterCorTextoGrafico();
  const corGrade = obterCorGradeGrafico();
  const temEixos = tipo === 'bar' || tipo === 'line';

  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: extras.legenda ?? tipo === 'doughnut',
        position: extras.posicaoLegenda || 'right',
        labels: {
          color: corTexto,
          font: { family: 'Inter', size: 12, weight: '600' },
          boxWidth: 12,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: document.body.classList.contains('dark-theme') ? '#0f172a' : '#ffffff',
        titleColor: document.body.classList.contains('dark-theme') ? '#f8fafc' : '#0f172a',
        bodyColor: corTexto,
        borderColor: obterCorGradeGrafico(),
        borderWidth: 1,
        padding: 12,
        callbacks: extras.callbacks || {}
      }
    },
    scales: temEixos ? {
      x: {
        ticks: { color: corTexto, font: { family: 'Inter', size: 11, weight: '600' } },
        grid: { display: extras.gridX ?? false, color: corGrade }
      },
      y: {
        ticks: { color: corTexto, font: { family: 'Inter', size: 11, weight: '600' } },
        grid: { color: corGrade },
        beginAtZero: true
      }
    } : {}
  };
}

function renderizarGraficoEvolucao() {
  criarGrafico('evolucao', 'chartEvolucao', {
    type: 'bar',
    data: {
      labels: ['Pix', 'TED', 'Boleto', 'Cartão', 'Saque', 'Open Finance'],
      datasets: [{
        label: 'Tentativas retidas',
        data: [120, 45, 18, 80, 9, 31],
        backgroundColor: ['#002776', '#003c9e', '#f8c200', '#06b6d4', '#f59e0b', '#ef4444'],
        borderRadius: 10,
        maxBarThickness: 54
      }]
    },
    options: montarOpcoesGrafico('bar', {
      legenda: false,
      callbacks: {
        label: contexto => ` ${formatarNumero(contexto.parsed.y)} tentativas`
      }
    })
  });
}

function renderizarGraficoRisco() {
  const baixo = estado.filaRisco.filter(item => item.risco === 'Baixo').length;
  const medio = estado.filaRisco.filter(item => item.risco === 'Médio').length;
  const alto = estado.filaRisco.filter(item => item.risco === 'Alto').length;

  criarGrafico('risco', 'chartRisco', {
    type: 'doughnut',
    data: {
      labels: ['Baixo', 'Médio', 'Alto'],
      datasets: [{
        data: [baixo, medio, alto],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: montarOpcoesGrafico('doughnut', { legenda: false })
  });
}

function renderizarGraficoClusters() {
  criarGrafico('clusters', 'chartClusters', {
    type: 'doughnut',
    data: {
      labels: ['Tráfego limpo', 'Comportamento suspeito', 'Fraude detectada', 'Revisão manual'],
      datasets: [{
        data: [62, 22, 10, 6],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#06b6d4'],
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: montarOpcoesGrafico('doughnut', { legenda: true, posicaoLegenda: 'bottom' })
  });
}

function renderizarGraficosDaPaginaAtual() {
  if (estado.paginaAtual === 'view-dashboard') {
    renderizarGraficoEvolucao();
    renderizarGraficoRisco();
  }

  if (estado.paginaAtual === 'view-aicore') {
    renderizarGraficoClusters();
  }
}

function mudarAba(idAlvo, titulo) {
  const paginaAlvo = document.getElementById(idAlvo);
  if (!paginaAlvo) return;

  document.querySelectorAll('.page').forEach(pagina => pagina.classList.remove('active'));
  paginaAlvo.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(botao => {
    const ativo = botao.dataset.page === idAlvo;
    botao.classList.toggle('active', ativo);
    botao.setAttribute('aria-selected', ativo ? 'true' : 'false');
  });

  const tituloPagina = document.getElementById('tituloPagina');
  if (tituloPagina) tituloPagina.textContent = titulo || 'Painel de Auditoria';

  estado.paginaAtual = idAlvo;
  destruirTodosGraficos();
  window.requestAnimationFrame(renderizarGraficosDaPaginaAtual);
  fecharSidebarMobile();
}

function alternarTema() {
  const botaoToggle = document.getElementById('btnTema');
  const textoLabel = document.getElementById('textoTema');
  const temaEscuroAtivo = Boolean(botaoToggle && botaoToggle.checked);

  document.body.classList.toggle('dark-theme', temaEscuroAtivo);

  if (textoLabel) {
    textoLabel.textContent = temaEscuroAtivo ? 'Tema Escuro' : 'Tema Claro';
  }

  destruirTodosGraficos();
  window.requestAnimationFrame(renderizarGraficosDaPaginaAtual);
}

function obterClasseRisco(risco) {
  if (risco === 'Alto') return 'pill-danger';
  if (risco === 'Médio') return 'pill-warning';
  return 'pill-success';
}

function obterClasseStatus(status) {
  if (String(status).toLowerCase().includes('pendente') || String(status).toLowerCase().includes('atrasado')) return 'pill-danger';
  if (String(status).toLowerCase().includes('análise') || String(status).toLowerCase().includes('atenção')) return 'pill-warning';
  return 'pill-success';
}

function filtrarFilaRisco() {
  const busca = document.getElementById('campoBuscaRisco')?.value.trim().toLowerCase() || '';
  const riscoSelecionado = document.getElementById('filtroRisco')?.value || 'Todos';

  return estado.filaRisco.filter(item => {
    const textoBusca = `${item.id} ${item.alvo} ${item.conta} ${item.canal} ${item.status} ${item.cidade} ${item.dispositivo}`.toLowerCase();
    const bateBusca = !busca || textoBusca.includes(busca);
    const bateRisco = riscoSelecionado === 'Todos' || item.risco === riscoSelecionado;
    return bateBusca && bateRisco;
  });
}

function carregarTabelaFilaRisco() {
  const corpo = document.getElementById('tabelaFilaRisco');
  const badge = document.getElementById('badgeFilaRisco');
  if (!corpo) return;

  const dados = filtrarFilaRisco();
  if (badge) badge.textContent = `${dados.length} registros`;

  if (dados.length === 0) {
    corpo.innerHTML = '<tr><td class="empty-state" colspan="8">Nenhuma ocorrência encontrada para os filtros selecionados.</td></tr>';
    return;
  }

  corpo.innerHTML = dados.map(item => `
    <tr>
      <td class="hash-mono">${escaparHTML(item.id)}</td>
      <td><strong>${escaparHTML(item.alvo)}</strong><br><span class="hash-mono">${escaparHTML(item.horario)} · ${escaparHTML(item.cidade)}</span></td>
      <td class="hash-mono">${escaparHTML(item.conta)}</td>
      <td>${escaparHTML(item.canal)}</td>
      <td class="hash-mono">${formatarMoeda(item.valor)}</td>
      <td><span class="pill ${obterClasseRisco(item.risco)}">${item.score} pts · ${escaparHTML(item.risco)}</span></td>
      <td><span class="pill ${obterClasseStatus(item.status)}">${escaparHTML(item.status)}</span></td>
      <td class="text-right">
        <button class="btn-action-outline success" type="button" data-action="liberar" data-id="${escaparHTML(item.id)}">Liberar</button>
        <button class="btn-action-outline danger" type="button" data-action="bloquear" data-id="${escaparHTML(item.id)}">Bloquear</button>
      </td>
    </tr>
  `).join('');
}

function carregarTabelaHardwares() {
  const corpo = document.getElementById('tabelaHardwares');
  if (!corpo) return;

  corpo.innerHTML = estado.dispositivos.map(item => `
    <tr>
      <td class="hash-mono">${escaparHTML(item.conta)}</td>
      <td>${escaparHTML(item.hardware)}</td>
      <td>${escaparHTML(item.localizacao)}</td>
      <td><span class="pill ${item.status.includes('Crítico') ? 'pill-danger' : item.status.includes('Observação') ? 'pill-warning' : 'pill-success'}">${escaparHTML(item.status)}</span></td>
    </tr>
  `).join('');
}

function carregarTabelaSla() {
  const corpo = document.getElementById('tabelaAuditoriaSla');
  if (!corpo) return;

  corpo.innerHTML = estado.sla.map(item => `
    <tr>
      <td class="hash-mono">${escaparHTML(item.ref)}</td>
      <td><strong>${escaparHTML(item.analista)}</strong></td>
      <td class="hash-mono">${escaparHTML(item.tempo)}</td>
      <td><span class="pill ${obterClasseStatus(item.status)}">${escaparHTML(item.status)}</span></td>
    </tr>
  `).join('');
}

function carregarTabelaBloqueios() {
  const corpo = document.getElementById('tabelaBloqueios');
  const badge = document.getElementById('badgeBloqueios');
  if (!corpo) return;

  if (badge) badge.textContent = `${estado.bloqueios.length} bloqueios`;

  if (estado.bloqueios.length === 0) {
    corpo.innerHTML = '<tr><td class="empty-state" colspan="6">Nenhuma conta bloqueada no momento.</td></tr>';
    return;
  }

  corpo.innerHTML = estado.bloqueios.map(item => `
    <tr>
      <td class="hash-mono">${escaparHTML(item.conta)}</td>
      <td><strong>${escaparHTML(item.titular)}</strong></td>
      <td>${escaparHTML(item.motivo)}</td>
      <td>${escaparHTML(item.origem)}</td>
      <td class="hash-mono">${escaparHTML(item.dataHora)}</td>
      <td class="text-right">
        <button class="btn-action-outline success" type="button" data-action="desbloquear" data-conta="${escaparHTML(item.conta)}">Desbloquear</button>
      </td>
    </tr>
  `).join('');
}

function carregarTabelaIaAlvos() {
  const corpo = document.getElementById('tabelaIaAlvos');
  if (!corpo) return;

  corpo.innerHTML = estado.iaAlvos.map(item => `
    <tr>
      <td><strong>${escaparHTML(item.alvo)}</strong></td>
      <td class="hash-mono" style="color: var(--info); font-weight: 800;">${escaparHTML(item.score)}</td>
      <td>${escaparHTML(item.acao)}</td>
      <td><span class="pill ${item.confianca === 'Alta' ? 'pill-danger' : item.confianca === 'Média' ? 'pill-warning' : 'pill-success'}">${escaparHTML(item.confianca)}</span></td>
    </tr>
  `).join('');
}

function carregarLogsIa() {
  const lista = document.getElementById('listaLogsIa');
  if (!lista) return;

  lista.innerHTML = estado.logsIa.map(item => `
    <article class="ai-log-card">
      <strong>${escaparHTML(item.titulo)}</strong>
      <p>${escaparHTML(item.texto)}</p>
    </article>
  `).join('');
}

function carregarJustificativas() {
  const corpo = document.getElementById('tabelaJustificativas');
  if (!corpo) return;

  if (estado.justificativas.length === 0) {
    corpo.innerHTML = '<tr><td class="empty-state" colspan="4">Nenhuma justificativa registrada nesta sessão.</td></tr>';
    return;
  }

  corpo.innerHTML = estado.justificativas.map(item => `
    <tr>
      <td class="hash-mono">${escaparHTML(item.horario)}</td>
      <td>${escaparHTML(item.analista)}</td>
      <td><span class="pill ${item.acao.includes('Bloqueio') ? 'pill-danger' : 'pill-info'}">${escaparHTML(item.acao)}</span></td>
      <td>${escaparHTML(item.justificativa)}</td>
    </tr>
  `).join('');
}

function atualizarKpis() {
  const transacoesSuspeitas = estado.filaRisco.filter(item => item.risco !== 'Baixo').length;
  const bloqueios = estado.bloqueios.length;
  const slaMinutos = estado.sla.map(item => Number.parseInt(item.tempo, 10)).filter(Number.isFinite);
  const mediaSla = slaMinutos.length ? Math.round(slaMinutos.reduce((acc, valor) => acc + valor, 0) / slaMinutos.length) : 0;

  const kpiVolume = document.getElementById('kpiVolumeSuspeito');
  const kpiBloqueios = document.getElementById('kpiBloqueios');
  const kpiSla = document.getElementById('kpiSlaMedio');

  if (kpiVolume) kpiVolume.textContent = formatarNumero(transacoesSuspeitas);
  if (kpiBloqueios) kpiBloqueios.textContent = formatarNumero(bloqueios);
  if (kpiSla) kpiSla.textContent = `${mediaSla}m`;
}

function carregarTodasTabelas() {
  carregarTabelaFilaRisco();
  carregarTabelaHardwares();
  carregarTabelaSla();
  carregarTabelaBloqueios();
  carregarTabelaIaAlvos();
  carregarLogsIa();
  carregarJustificativas();
  atualizarKpis();
}

function mostrarAlerta(mensagem) {
  const caixa = document.getElementById('toastBox');
  if (!caixa) return;

  caixa.textContent = mensagem;
  caixa.classList.add('show');

  window.clearTimeout(mostrarAlerta.timeoutId);
  mostrarAlerta.timeoutId = window.setTimeout(() => {
    caixa.classList.remove('show');
  }, 3200);
}

function registrarJustificativa(acao, justificativa, analista = 'Victor Daniel') {
  const agora = new Date();
  estado.justificativas.unshift({
    horario: agora.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    analista,
    acao,
    justificativa
  });
  carregarJustificativas();
}

async function bloquearTransacao(id) {
  const transacao = estado.filaRisco.find(item => String(item.id) === String(id));
  if (!transacao) return;

  const justificativa = `Bloqueio preventivo da ocorrência ${transacao.id} pelo painel do analista.`;
  let backendConfirmado = false;

  if (transacao.backendId) {
    try {
      const resposta = await fetch(`${API_BASE_URL}/analise/contas/bloquear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conta: transacao.conta,
          transacao_id: transacao.backendId,
          justificativa,
          analista: 'Victor Daniel'
        })
      });
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(dados.detail || dados.mensagem || 'Falha ao bloquear no back-end.');
      backendConfirmado = true;
    } catch (erro) {
      console.error('Erro no bloqueio via API:', erro);
      mostrarAlerta(`API indisponível para bloqueio. Aplicando mock local: ${erro.message}`);
    }
  }

  transacao.status = 'Conta bloqueada';
  transacao.risco = transacao.risco === 'Baixo' ? 'Médio' : transacao.risco;

  const jaBloqueada = estado.bloqueios.some(item => item.conta === transacao.conta);
  if (!jaBloqueada) {
    estado.bloqueios.unshift({
      conta: transacao.conta,
      titular: transacao.alvo,
      motivo: justificativa,
      origem: backendConfirmado ? 'Back-end' : 'Mock local',
      dataHora: new Date().toLocaleString('pt-BR')
    });
  }

  registrarJustificativa('Bloqueio preventivo', justificativa);
  carregarTodasTabelas();
  destruirTodosGraficos();
  renderizarGraficosDaPaginaAtual();
  mostrarAlerta(`Ocorrência ${id} bloqueada com sucesso.`);

  if (backendConfirmado) {
    await sincronizarComBackend(false);
  }
}

async function liberarTransacao(id) {
  const transacao = estado.filaRisco.find(item => String(item.id) === String(id));
  if (!transacao) return;

  const justificativa = `Aprovação manual da ocorrência ${transacao.id} após revisão do analista.`;
  let backendConfirmado = false;

  if (transacao.backendId) {
    try {
      const resposta = await fetch(`${API_BASE_URL}/analise/transacoes/${transacao.backendId}/aprovar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ justificativa, analista: 'Victor Daniel' })
      });
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(dados.detail || dados.mensagem || 'Falha ao aprovar no back-end.');
      backendConfirmado = true;
    } catch (erro) {
      console.error('Erro na aprovação via API:', erro);
      mostrarAlerta(`API indisponível para aprovação. Aplicando mock local: ${erro.message}`);
    }
  }

  transacao.status = 'Aprovada';
  transacao.risco = transacao.score >= 70 ? 'Médio' : 'Baixo';

  registrarJustificativa('Liberação manual', justificativa);
  carregarTodasTabelas();
  destruirTodosGraficos();
  renderizarGraficosDaPaginaAtual();
  mostrarAlerta(`Ocorrência ${id} liberada para processamento.`);

  if (backendConfirmado) {
    await sincronizarComBackend(false);
  }
}

async function desbloquearConta(conta) {
  const justificativa = `Conta ${conta} desbloqueada após validação manual pelo painel do analista.`;
  let backendConfirmado = false;

  try {
    const resposta = await fetch(`${API_BASE_URL}/analise/contas/desbloquear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conta, justificativa, analista: 'Victor Daniel' })
    });
    const dados = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(dados.detail || dados.mensagem || 'Falha ao desbloquear no back-end.');
    backendConfirmado = true;
  } catch (erro) {
    console.error('Erro no desbloqueio via API:', erro);
    mostrarAlerta(`API indisponível para desbloqueio. Aplicando mock local: ${erro.message}`);
  }

  estado.bloqueios = estado.bloqueios.filter(item => item.conta !== conta);
  estado.filaRisco.forEach(item => {
    if (item.conta === conta && item.status === 'Conta bloqueada') {
      item.status = 'Em análise';
    }
  });
  registrarJustificativa('Desbloqueio de conta', justificativa);
  carregarTodasTabelas();
  destruirTodosGraficos();
  renderizarGraficosDaPaginaAtual();
  mostrarAlerta(`Conta ${conta} desbloqueada.`);

  if (backendConfirmado) {
    await sincronizarComBackend(false);
  }
}

async function lidarComCliqueDeAcao(evento) {
  const botao = evento.target.closest('button[data-action]');
  if (!botao) return;

  evento.preventDefault();
  botao.disabled = true;
  const textoOriginal = botao.textContent;
  botao.textContent = 'Processando...';

  try {
    const acao = botao.dataset.action;
    if (acao === 'bloquear') await bloquearTransacao(botao.dataset.id);
    if (acao === 'liberar') await liberarTransacao(botao.dataset.id);
    if (acao === 'desbloquear') await desbloquearConta(botao.dataset.conta);
  } finally {
    botao.disabled = false;
    botao.textContent = textoOriginal;
  }
}

function configurarNavegacaoSpa() {
  const botoesNavegacao = document.querySelectorAll('.nav-item, .btn-aicore-trigger');
  botoesNavegacao.forEach(botao => {
    botao.addEventListener('click', evento => {
      evento.preventDefault();
      const idAlvo = botao.dataset.page;
      const titulo = botao.dataset.title;
      mudarAba(idAlvo, titulo);
    });
  });
}

function configurarTema() {
  const botaoTema = document.getElementById('btnTema');
  if (!botaoTema) return;

  botaoTema.checked = document.body.classList.contains('dark-theme');
  botaoTema.addEventListener('change', alternarTema);
  alternarTema();
}

function configurarFiltros() {
  const campoBusca = document.getElementById('campoBuscaRisco');
  const filtroRisco = document.getElementById('filtroRisco');
  const botaoFiltrar = document.getElementById('btnFiltrarRisco');
  const botaoLimpar = document.getElementById('btnLimparFiltroRisco');

  if (campoBusca) {
    campoBusca.addEventListener('input', carregarTabelaFilaRisco);
  }

  if (filtroRisco) {
    filtroRisco.addEventListener('change', carregarTabelaFilaRisco);
  }

  if (botaoFiltrar) {
    botaoFiltrar.addEventListener('click', () => {
      carregarTabelaFilaRisco();
      mostrarAlerta('Filtros aplicados na fila de risco.');
    });
  }

  if (botaoLimpar) {
    botaoLimpar.addEventListener('click', () => {
      if (campoBusca) campoBusca.value = '';
      if (filtroRisco) filtroRisco.value = 'Todos';
      carregarTabelaFilaRisco();
      mostrarAlerta('Filtros removidos.');
    });
  }
}

function configurarBotoesAicore() {
  const botaoRelatorio = document.getElementById('btnGerarRelatorio');
  const botaoReprocessar = document.getElementById('btnReprocessarIa');

  if (botaoRelatorio) {
    botaoRelatorio.addEventListener('click', () => mostrarAlerta('Relatório AICore gerado com sucesso.'));
  }

  if (botaoReprocessar) {
    botaoReprocessar.addEventListener('click', () => {
      renderizarGraficoClusters();
      mostrarAlerta('Matriz neural reprocessada com os dados atuais.');
    });
  }
}

function abrirSidebarMobile() {
  document.getElementById('sidebar')?.classList.add('open');
  document.getElementById('overlay')?.classList.add('show');
}

function fecharSidebarMobile() {
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('overlay')?.classList.remove('show');
}

function configurarMenuMobile() {
  document.getElementById('menuBtn')?.addEventListener('click', abrirSidebarMobile);
  document.getElementById('sidebarClose')?.addEventListener('click', fecharSidebarMobile);
  document.getElementById('overlay')?.addEventListener('click', fecharSidebarMobile);
}

function atualizarDataCabecalho() {
  const elemento = document.getElementById('headerDate');
  if (!elemento) return;

  const agora = new Date();
  elemento.textContent = agora.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  });
}

function extrairLista(payload, chavePreferencial) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload[chavePreferencial])) return payload[chavePreferencial];

  const primeiraLista = Object.values(payload).find(valor => Array.isArray(valor));
  return primeiraLista || [];
}

function extrairIdNumerico(valor) {
  if (typeof valor === 'number') return valor;
  const texto = String(valor || '');
  const encontrado = texto.match(/\d+/);
  return encontrado ? Number(encontrado[0]) : null;
}

function normalizarTransacaoBackend(transacao) {
  const riscoBruto = transacao.risco?.nivel || transacao.classificacao_risco || transacao.risco || 'Baixo';
  const risco = riscoBruto === 'vermelho' ? 'Alto' : riscoBruto === 'amarelo' ? 'Médio' : riscoBruto === 'verde' ? 'Baixo' : riscoBruto;
  const score = transacao.risco?.pontos || transacao.score || transacao.pontos_risco || transacao.pontos || (risco === 'Alto' ? 90 : risco === 'Médio' ? 55 : 22);
  const backendId = transacao.id || transacao.transacao_id || extrairIdNumerico(transacao.ref);

  return {
    id: backendId ? `TX-${backendId}` : `TX-${Date.now()}`,
    backendId,
    alvo: transacao.titular || transacao.cliente || transacao.cpf || transacao.conta || 'Cliente não identificado',
    conta: transacao.conta || transacao.conta_origem || '—',
    canal: transacao.tipo_transacao || transacao.categoria || 'Transação',
    valor: Number(transacao.valor || 0),
    score,
    risco,
    status: transacao.status_analise || transacao.status_transacao || transacao.status || 'Pendente',
    cidade: transacao.cidade || '—',
    dispositivo: transacao.dispositivo || '—',
    horario: transacao.hora || '--:--'
  };
}

async function sincronizarComBackend(exibirToastInicial = true) {
  if (exibirToastInicial) mostrarAlerta('Tentando sincronizar com a API local...');

  try {
    const [transacoesResposta, dispositivosResposta, slaResposta, bloqueiosResposta, justificativasResposta] = await Promise.allSettled([
      fetch(`${API_BASE_URL}/analise/transacoes?risco=Todos`),
      fetch(`${API_BASE_URL}/analise/dispositivos`),
      fetch(`${API_BASE_URL}/analise/sla`),
      fetch(`${API_BASE_URL}/analise/contas/bloqueadas`),
      fetch(`${API_BASE_URL}/analise/logs/justificativas?limite=30`)
    ]);

    if (transacoesResposta.status === 'fulfilled' && transacoesResposta.value.ok) {
      const payload = await transacoesResposta.value.json();
      const transacoes = extrairLista(payload, 'transacoes');
      if (transacoes.length > 0) {
        estado.filaRisco = transacoes.map(normalizarTransacaoBackend);
      }
    }

    if (dispositivosResposta.status === 'fulfilled' && dispositivosResposta.value.ok) {
      const payload = await dispositivosResposta.value.json();
      const dispositivos = extrairLista(payload, 'dispositivos');
      if (dispositivos.length > 0) {
        estado.dispositivos = dispositivos.map(item => ({
          conta: item.conta || '—',
          hardware: `${item.dispositivo || item.hardware || 'Dispositivo'} · ${item.ip || 'IP não informado'}`,
          localizacao: item.localizacao || item.cidade || '—',
          status: item.confiavel === 'Sim' || item.status === 'Confiável' ? 'Confiável' : item.confiavel === 'Parcial' ? 'Observação' : 'Alerta Crítico'
        }));
      }
    }

    if (slaResposta.status === 'fulfilled' && slaResposta.value.ok) {
      const payload = await slaResposta.value.json();
      const sla = extrairLista(payload, 'casos');
      if (sla.length > 0) {
        estado.sla = sla.map(item => ({
          ref: item.id ? `CASO-${item.id}` : item.ref || 'CASO',
          analista: item.analista || 'Analista',
          tempo: item.tempo ? `${item.tempo}m` : item.tempo_minutos ? `${item.tempo_minutos}m` : '1m',
          status: item.status || item.sla_status || 'Dentro do prazo'
        }));
      }
    }

    if (bloqueiosResposta.status === 'fulfilled' && bloqueiosResposta.value.ok) {
      const payload = await bloqueiosResposta.value.json();
      const bloqueios = extrairLista(payload, 'bloqueadas');
      estado.bloqueios = bloqueios.map(item => ({
        conta: item.conta || item.id || '—',
        titular: item.titular || item.cliente || item.conta || 'Cliente',
        motivo: item.motivo || 'Bloqueio preventivo',
        origem: item.origem || item.analista || 'Back-end',
        dataHora: item.dataHora || item.data_hora || new Date().toLocaleString('pt-BR')
      }));
    }

    if (justificativasResposta.status === 'fulfilled' && justificativasResposta.value.ok) {
      const payload = await justificativasResposta.value.json();
      const justificativas = extrairLista(payload, 'logs');
      if (justificativas.length > 0) {
        estado.justificativas = justificativas.map(item => ({
          horario: item.data_hora || item.horario || '--:--',
          analista: item.analista || 'Analista',
          acao: item.acao || 'Auditoria',
          justificativa: item.justificativa || item.detalhe || 'Registro sem detalhe.'
        }));
      }
    }

    carregarTodasTabelas();
    destruirTodosGraficos();
    renderizarGraficosDaPaginaAtual();
    mostrarAlerta('Sincronização concluída. Dados do painel atualizados.');
  } catch (erro) {
    console.error('Erro ao sincronizar com o back-end:', erro);
    mostrarAlerta('Não foi possível conectar à API. Mantendo mocks locais.');
  }

  // Ligação permanente com Back-end:
  // As rotas /analise/transacoes, /analise/dispositivos, /analise/sla,
  // /analise/contas/bloqueadas e /analise/logs/justificativas são consumidas aqui.
}

function configurarSincronizacaoApi() {
  document.getElementById('btnSincronizarApi')?.addEventListener('click', sincronizarComBackend);

  if (USAR_BACKEND_AUTOMATICAMENTE) {
    sincronizarComBackend();
  }
}

function iniciarAplicacao() {
  configurarNavegacaoSpa();
  configurarTema();
  configurarFiltros();
  configurarBotoesAicore();
  configurarMenuMobile();
  configurarSincronizacaoApi();
  document.body.addEventListener('click', lidarComCliqueDeAcao);
  atualizarDataCabecalho();
  carregarTodasTabelas();
  renderizarGraficosDaPaginaAtual();
}

document.addEventListener('DOMContentLoaded', iniciarAplicacao);
