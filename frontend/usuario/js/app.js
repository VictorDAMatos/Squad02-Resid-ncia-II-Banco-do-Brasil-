
const API_BASE = 'http://127.0.0.1:8000';

const state = {
  balance: 0,
  balanceVisible: true,
  activeFilter: 'all',
  pendingTransfer: null,
  user: { name: '', account: '', agency: '' },
  transactions: [],
};

function formatCurrency(val) {
  return Number(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T'));
  const diff  = Date.now() - date.getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  const hm    = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  if (mins  < 1)   return 'Agora mesmo';
  if (mins  < 60)  return `${mins} min atrás`;
  if (hours < 24)  return `Hoje, ${hm}`;
  if (days  === 1) return `Ontem, ${hm}`;
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) + ', ' + hm;
}

function showToast(msg, duration = 3200) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function showError(msg) {
  document.getElementById('errorMsg').innerHTML = msg.replace(/\n/g, '<br>');
  openModal('modal-error');
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Erro na requisição.');
  }
  return res.json();
}

async function carregarPerfil() {
  try {
    const perfil = await apiFetch('/usuario/perfil');
    state.user = { name: perfil.nome, account: perfil.conta, agency: perfil.agencia };

    const firstName = perfil.nome.split(' ')[0];
    setGreeting(firstName);

    const userNameEl = document.querySelector('.user-name');
    if (userNameEl) userNameEl.textContent = perfil.nome;

    const userAccEl = document.querySelector('.user-account');
    if (userAccEl) userAccEl.textContent = `Ag. ${perfil.agencia} · CC ${perfil.conta}`;
  } catch (e) {
    console.warn('Perfil não carregado:', e.message);
  }
}

async function carregarSaldo() {
  try {
    const data = await apiFetch('/usuario/saldo');
    state.balance = data.saldo;
    renderBalance();
    updateBalanceBar(data);
  } catch (e) {
    showToast('Erro ao carregar saldo: ' + e.message);
  }
}

function renderBalance() {
  const display = document.getElementById('balanceDisplay');
  const formBal = document.getElementById('formBalance');
  const val = formatCurrency(state.balance);
  if (display) display.textContent = state.balanceVisible ? val : '•••••••';
  if (formBal) formBal.textContent = val;
}

function updateBalanceBar(data) {
  if (!data) return;
  const fill    = document.getElementById('balanceBarFill');
  const pctEl   = document.getElementById('limitPct');
  const limitEl = document.getElementById('limitDisplay');
  if (fill)    fill.style.width = `${data.percentual_usado}%`;
  if (pctEl)   pctEl.textContent = `${data.percentual_usado}% utilizado`;
  if (limitEl) limitEl.textContent = formatCurrency(data.limite_disponivel);

  if (data.alerta_critico) {
    addAlert('danger', 'danger', 'Limite crítico',
      `Você utilizou ${data.percentual_usado}% do seu limite de crédito. Considere um depósito.`);
  }
}

document.getElementById('toggleBalance').addEventListener('click', () => {
  state.balanceVisible = !state.balanceVisible;
  renderBalance();
  const icon = document.getElementById('eyeIcon');
  if (icon) {
    icon.innerHTML = state.balanceVisible
      ? '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'
      : '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
  }
});

async function carregarTransacoes(tipo = null) {
  try {
    const params = tipo && tipo !== 'all' ? `?tipo=${tipo}&limite=50` : '?limite=50';
    const data   = await apiFetch(`/usuario/transacoes${params}`);
    state.transactions = data.transacoes;
    return data.transacoes;
  } catch (e) {
    showToast('Erro ao carregar transações: ' + e.message);
    return [];
  }
}

const txLabels = { sent: 'D', received: 'C', deposit: 'C', pix: 'D' };

function buildTxItem(tx) {
  const tipo  = tx.tipo || tx.tipo_transacao || 'deposit';
  const nome  = tx.nome || tx.dispositivo || '—';
  const desc  = tx.descricao || tx.categoria || '';
  const valor = tx.valor || 0;
  const data  = tx.data_hora || tx.data || '';

  const div = document.createElement('div');
  div.className = 'tx-item';
  div.innerHTML = `
    <div class="tx-icon ${tipo}">${txLabels[tipo] || 'C'}</div>
    <div class="tx-info">
      <div class="tx-name">${nome}</div>
      <div class="tx-date">${desc ? desc + ' · ' : ''}${formatDate(data)}</div>
    </div>
    <div class="tx-amount ${tipo}">
      ${tipo === 'sent' || tipo === 'pix' ? '−' : '+'}${formatCurrency(valor)}
    </div>
  `;
  return div;
}

async function renderRecentTransactions() {
  const c = document.getElementById('recentTransactions');
  if (!c) return;
  c.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;padding:8px 0;">Carregando...</p>';
  const txs = await carregarTransacoes();
  c.innerHTML = '';
  txs.slice(0, 5).forEach(tx => c.appendChild(buildTxItem(tx)));
}

async function renderHistory() {
  const c = document.getElementById('historyTransactions');
  if (!c) return;
  c.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;padding:8px 0;">Carregando...</p>';
  const txs = await carregarTransacoes(state.activeFilter);
  c.innerHTML = '';
  if (!txs.length) {
    c.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;padding:16px 0;">Nenhuma movimentação encontrada.</p>';
    return;
  }
  txs.forEach(tx => c.appendChild(buildTxItem(tx)));
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.activeFilter = btn.dataset.filter;
    renderHistory();
  });
});

async function exportTransactions() {
  try {
    const tipo   = state.activeFilter !== 'all' ? `?tipo=${state.activeFilter}` : '';
    const res    = await fetch(`${API_BASE}/usuario/extrato/exportar${tipo}`);
    if (!res.ok) { showToast('Nenhuma transação para exportar.'); return; }
    const blob   = await res.blob();
    const url    = URL.createObjectURL(blob);
    const link   = document.createElement('a');
    link.href     = url;
    link.download = `extrato-bb-${state.activeFilter}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    showToast('Extrato exportado com sucesso.');
  } catch (e) {
    showToast('Erro ao exportar: ' + e.message);
  }
}

function validateTransfer({ recipientName, recipientAccount, amount }) {
  const errors = [];
  if (!recipientName.trim())    errors.push('Informe o nome do favorecido.');
  if (!recipientAccount.trim()) errors.push('Informe a agência e conta do favorecido.');
  if (!amount || isNaN(amount) || amount <= 0) errors.push('Informe um valor válido.');
  return errors;
}

function initiateTransfer() {
  const recipientName    = document.getElementById('recipientName').value;
  const recipientAccount = document.getElementById('recipientAccount').value;
  const amount           = parseFloat(document.getElementById('transferAmount').value);
  const description      = document.getElementById('transferDesc').value;

  const errors = validateTransfer({ recipientName, recipientAccount, amount });
  if (errors.length > 0) { showError(errors.join('\n')); return; }

  state.pendingTransfer = { recipientName, recipientAccount, amount, description };

  const details = document.getElementById('modalDetails');
  details.innerHTML = `
    <div class="modal-detail-row"><span>Favorecido</span><span>${recipientName}</span></div>
    <div class="modal-detail-row"><span>Conta/Agência</span><span>${recipientAccount}</span></div>
    <div class="modal-detail-row"><span>Valor</span><span style="color:var(--bb-blue);font-size:1rem;font-weight:700">${formatCurrency(amount)}</span></div>
    <div class="modal-detail-row"><span>Finalidade</span><span>${description || '—'}</span></div>
    <div class="modal-detail-row"><span>Saldo após operação</span><span>${formatCurrency(state.balance - amount)}</span></div>
  `;

  if (amount >= 1000) {
    addAlert('danger', 'danger', 'Atenção: valor elevado',
      `Você está prestes a transferir ${formatCurrency(amount)}. Confirme os dados do favorecido.`);
  }

  openModal('modal-confirm');
}

async function confirmTransfer() {
  const tx = state.pendingTransfer;
  if (!tx) return;

  try {
    const resp = await apiFetch('/usuario/transferencia', {
      method: 'POST',
      body: JSON.stringify({
        nome_favorecido:  tx.recipientName,
        conta_favorecido: tx.recipientAccount,
        valor:            tx.amount,
        descricao:        tx.description || 'Transferência',
      }),
    });

    state.balance = resp.saldo_apos;
    renderBalance();
    renderRecentTransactions();
    await carregarSaldo();

    addAlert('success', 'success', 'Transferência realizada',
      `Débito de ${formatCurrency(tx.amount)} para ${tx.recipientName} confirmado.`);

    ['recipientName','recipientAccount','transferAmount','transferDesc'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });

    closeModal('modal-confirm');

    document.getElementById('successMsg').textContent =
      `${formatCurrency(tx.amount)} transferidos para ${tx.recipientName} com sucesso.`;
    document.getElementById('protocolNum').textContent = resp.protocolo;
    openModal('modal-success');

    state.pendingTransfer = null;
  } catch (e) {
    closeModal('modal-confirm');
    showError(e.message);
  }
}

function openPixModal() { openModal('modal-pix'); }

async function processPix() {
  const key    = document.getElementById('pixKey').value.trim();
  const amount = parseFloat(document.getElementById('pixAmount').value);

  if (!key)                   { showToast('Informe a chave Pix do destinatário.'); return; }
  if (!amount || amount <= 0) { showToast('Informe um valor válido.'); return; }

  try {
    const resp = await apiFetch('/usuario/pix', {
      method: 'POST',
      body: JSON.stringify({ chave_pix: key, valor: amount, descricao: 'Pix enviado' }),
    });

    state.balance = resp.saldo_apos;
    renderBalance();
    renderRecentTransactions();
    await carregarSaldo();

    document.getElementById('pixKey').value    = '';
    document.getElementById('pixAmount').value = '';
    closeModal('modal-pix');
    showToast(`Pix de ${formatCurrency(amount)} realizado com sucesso. Protocolo: ${resp.protocolo}`);
  } catch (e) {
    showError(e.message);
  }
}

function openDepositModal() { openModal('modal-deposit'); }

async function processDeposit() {
  const amount = parseFloat(document.getElementById('depositAmount').value);
  if (!amount || amount <= 0) { showToast('Informe um valor válido.'); return; }

  try {
    const resp = await apiFetch('/usuario/deposito', {
      method: 'POST',
      body: JSON.stringify({ valor: amount }),
    });

    state.balance = resp.saldo_apos;
    renderBalance();
    renderRecentTransactions();
    await carregarSaldo();

    addAlert('success', 'success', 'Crédito recebido',
      `${formatCurrency(amount)} creditados na sua conta corrente.`);

    document.getElementById('depositAmount').value = '';
    closeModal('modal-deposit');
    showToast(`Crédito de ${formatCurrency(amount)} realizado com sucesso.`);
  } catch (e) {
    showError(e.message);
  }
}

function navigateTo(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const pageEl = document.getElementById(`page-${page}`);
  if (pageEl) pageEl.classList.add('active');

  const navEl = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (navEl) navEl.classList.add('active');

  closeSidebar();

  if (page === 'history')   renderHistory();
  if (page === 'dashboard') renderRecentTransactions();
}

function openSidebar()  { document.getElementById('sidebar').classList.add('open');    document.getElementById('overlay').classList.add('active'); }
function closeSidebar() { document.getElementById('sidebar').classList.remove('open'); document.getElementById('overlay').classList.remove('active'); }

document.getElementById('menuBtn').addEventListener('click', openSidebar);
document.getElementById('sidebarClose').addEventListener('click', closeSidebar);
document.getElementById('overlay').addEventListener('click', closeSidebar);

function updateClock() {
  const now = new Date();
  const el  = document.getElementById('currentTime');
  if (el) el.textContent = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}
updateClock();
setInterval(updateClock, 1000);

function setHeaderDate() {
  const el = document.getElementById('headerDate');
  if (!el) return;
  const now = new Date();
  const dia = now.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
  el.innerHTML = dia.charAt(0).toUpperCase() + dia.slice(1);
}
setHeaderDate();

function setGreeting(name) {
  const h = new Date().getHours();
  const g = h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite';
  const el = document.getElementById('greeting');
  if (el) el.textContent = `${g}, ${name || 'Julia'}`;
}

const alertTypeMap = {
  success: { cls: 'alert-success', iconCls: 'success', label: '✓' },
  danger:  { cls: 'alert-danger',  iconCls: 'danger',  label: '!' },
  warning: { cls: 'alert-warning', iconCls: 'warning', label: '!' },
  info:    { cls: 'alert-info',    iconCls: 'info',    label: 'i' },
};

function addAlert(type, iconType, title, message) {
  const container = document.getElementById('alertsContainer');
  if (!container) return;
  const { cls, iconCls, label } = alertTypeMap[type] || alertTypeMap.info;
  const div = document.createElement('div');
  div.className = `alert-item ${cls}`;
  div.innerHTML = `
    <div class="alert-icon-wrap ${iconCls}">${label}</div>
    <div class="alert-text">
      <strong>${title}</strong>
      <p>${message}</p>
    </div>
    <button class="alert-close" onclick="dismissAlert(this)">✕</button>
  `;
  container.insertBefore(div, container.firstChild);
  const badge = document.getElementById('notifBadge');
  if (badge) badge.textContent = parseInt(badge.textContent || '0') + 1;
}

function dismissAlert(btn) {
  const alert = btn.closest('.alert-item');
  alert.style.opacity   = '0';
  alert.style.transform = 'translateX(8px)';
  alert.style.transition = 'all 0.2s ease';
  setTimeout(() => alert.remove(), 220);
  const badge = document.getElementById('notifBadge');
  if (badge) badge.textContent = Math.max(0, parseInt(badge.textContent || '0') - 1);
}

document.getElementById('notifBell').addEventListener('click', () => {
  navigateTo('dashboard');
  setTimeout(() => {
    const el = document.querySelector('.alerts-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }, 100);
});

document.getElementById('darkModeToggle').addEventListener('change', e => {
  document.body.classList.toggle('dark', e.target.checked);
  showToast(e.target.checked ? 'Tema escuro ativado.' : 'Tema claro ativado.');
});

document.addEventListener('click', e => {
  const t = e.target.closest('[data-page]');
  if (t) { e.preventDefault(); navigateTo(t.dataset.page); }
});

document.querySelectorAll('.modal-backdrop').forEach(b => {
  b.addEventListener('click', e => { if (e.target === b) b.classList.remove('open'); });
});

document.querySelector('.btn-logout').addEventListener('click', () => {
  showToast('Sessão encerrada com segurança.');
  setTimeout(() => { window.location.href = '../login.html'; }, 1200);
});

(async function init() {
  await carregarPerfil();
  await carregarSaldo();
  await renderRecentTransactions();

  addAlert('info', 'info', 'Bem-vinda ao BB',
    'Seu Internet Banking está atualizado. Confira suas movimentações recentes.');
  addAlert('warning', 'warning', 'Fatura próxima',
    'O vencimento da sua fatura se aproxima. Evite juros pagando em dia.');
})();

function openBoletoModal() { openModal('modal-boleto'); }

async function gerarBoleto() {
  const beneficiario = document.getElementById('boletoNome').value.trim();
  const valor        = parseFloat(document.getElementById('boletoValor').value);
  const vencimento   = document.getElementById('boletoVencimento').value;

  if (!beneficiario) { showToast('Informe o beneficiário.'); return; }
  if (!valor || valor <= 0) { showToast('Informe um valor válido.'); return; }
  if (!vencimento) { showToast('Informe a data de vencimento.'); return; }

  try {
    const resp = await apiFetch('/usuario/boleto/gerar', {
      method: 'POST',
      body: JSON.stringify({ beneficiario, valor, vencimento }),
    });

    document.getElementById('boletoCodigoGerado').textContent = resp.codigo;
    document.getElementById('boletoResultado').style.display = 'block';
    showToast('Boleto gerado com sucesso!');
    await carregarBoletos();
  } catch (e) {
    showError(e.message);
  }
}

async function pagarBoleto() {
  const codigo = document.getElementById('boletoCodigo').value.trim();
  if (!codigo) { showToast('Informe o código do boleto.'); return; }

  try {
    const resp = await apiFetch('/usuario/boleto/pagar', {
      method: 'POST',
      body: JSON.stringify({ codigo }),
    });

    state.balance = resp.saldo_apos;
    renderBalance();
    await carregarSaldo();
    await renderRecentTransactions();

    document.getElementById('boletoCodigo').value = '';
    showToast(`Boleto de ${formatCurrency(resp.valor)} pago para ${resp.beneficiario}!`);
    await carregarBoletos();
  } catch (e) {
    showError(e.message);
  }
}

async function carregarBoletos() {
  try {
    const data = await apiFetch('/usuario/boleto/listar');
    const container = document.getElementById('boletoLista');
    if (!container) return;
    if (!data.boletos.length) {
      container.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;">Nenhum boleto encontrado.</p>';
      return;
    }
    container.innerHTML = data.boletos.map(b => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border);">
        <div>
          <div style="font-weight:600;font-size:0.85rem;">${b.beneficiario}</div>
          <div style="font-size:0.75rem;color:var(--text-muted);">Venc. ${b.vencimento}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-weight:700;color:var(--bb-blue);">${formatCurrency(b.valor)}</div>
          <span style="font-size:0.7rem;padding:2px 8px;border-radius:10px;background:${b.status==='pago'?'var(--green-light)':'var(--orange-light)'};color:${b.status==='pago'?'var(--green)':'var(--orange)'};">${b.status}</span>
        </div>
      </div>
    `).join('');
  } catch(e) { console.warn('Erro ao carregar boletos:', e.message); }
}

function openEmprestimoModal() { openModal('modal-emprestimo'); }

async function simularEmprestimo() {
  const valor    = parseFloat(document.getElementById('empValor').value);
  const parcelas = parseInt(document.getElementById('empParcelas').value);

  if (!valor || valor <= 0) { showToast('Informe um valor válido.'); return; }
  if (!parcelas) { showToast('Selecione o número de parcelas.'); return; }

  try {
    const resp = await apiFetch('/usuario/emprestimo/simular', {
      method: 'POST',
      body: JSON.stringify({ valor, parcelas }),
    });

    document.getElementById('empResultadoValor').textContent    = formatCurrency(resp.valor_parcela);
    document.getElementById('empResultadoParcelas').textContent = `${resp.parcelas}x de ${formatCurrency(resp.valor_parcela)}`;
    document.getElementById('empResultadoTotal').textContent    = formatCurrency(resp.total_pagar);
    document.getElementById('empResultadoTaxa').textContent     = `${resp.taxa_mensal}% a.m.`;
    document.getElementById('empResultado').style.display       = 'block';
    showToast('Simulação salva com sucesso!');
  } catch (e) {
    showError(e.message);
  }
}
