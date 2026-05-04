
const state = {
  balance: 1847.50,
  balanceVisible: true,
  activeFilter: 'all',
  pendingTransfer: null,

  user: {
    name: 'Julia Mendes',
    account: '58392-1',
    agency: '0042-3',
  },

  transactions: [
    { id: 1, type: 'received', name: 'Ana Lima',        description: 'Racha do almoço',         amount: 150.00, date: new Date(Date.now() - 2   * 3600000) },
    { id: 2, type: 'sent',     name: 'Spotify',          description: 'Assinatura mensal',        amount: 21.90,  date: new Date(Date.now() - 26  * 3600000) },
    { id: 3, type: 'sent',     name: 'Uber',             description: 'Viagem à faculdade',       amount: 18.50,  date: new Date(Date.now() - 50  * 3600000) },
    { id: 4, type: 'received', name: 'Mãe',              description: 'Mesada',                   amount: 800.00, date: new Date(Date.now() - 5   * 86400000) },
    { id: 5, type: 'sent',     name: 'Livraria Cultura', description: 'Livros de Direito Civil',  amount: 145.80, date: new Date(Date.now() - 7   * 86400000) },
    { id: 6, type: 'deposit',  name: 'Depósito',         description: 'Trabalho freelance',       amount: 300.00, date: new Date(Date.now() - 10  * 86400000) },
  ],
};

function formatCurrency(val) {
  return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatDate(date) {
  const diff  = Date.now() - date;
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  const hm    = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  if (mins  < 1)  return 'Agora mesmo';
  if (mins  < 60) return `${mins} min atrás`;
  if (hours < 24) return `Hoje, ${hm}`;
  if (days  === 1) return `Ontem, ${hm}`;
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) + ', ' + hm;
}

function genProtocol() {
  return 'BB' + Date.now().toString().slice(-8).toUpperCase();
}

function showToast(msg, duration = 3200) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

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

function openSidebar()  { document.getElementById('sidebar').classList.add('open');  document.getElementById('overlay').classList.add('active'); }
function closeSidebar() { document.getElementById('sidebar').classList.remove('open'); document.getElementById('overlay').classList.remove('active'); }

document.getElementById('menuBtn').addEventListener('click', openSidebar);
document.getElementById('sidebarClose').addEventListener('click', closeSidebar);
document.getElementById('overlay').addEventListener('click', closeSidebar);

function updateClock() {
  const now = new Date();
  document.getElementById('currentTime').textContent =
    now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
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

function setGreeting() {
  const h = new Date().getHours();
  const g = h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite';
  document.getElementById('greeting').textContent = `${g}, Julia`;
}
setGreeting();

const CREDIT_LIMIT = 3000;

function renderBalance() {
  const display = document.getElementById('balanceDisplay');
  const formBal = document.getElementById('formBalance');

  const val = formatCurrency(state.balance);
  display.textContent = state.balanceVisible ? val : '•••••••';
  if (formBal) formBal.textContent = val;
}

function updateBalanceBar() {
  const used = Math.max(0, CREDIT_LIMIT - state.balance);
  const pct  = Math.min(100, (used / CREDIT_LIMIT) * 100).toFixed(0);

  const fill    = document.getElementById('balanceBarFill');
  const pctEl   = document.getElementById('limitPct');
  const limitEl = document.getElementById('limitDisplay');

  if (fill)    fill.style.width = `${pct}%`;
  if (pctEl)   pctEl.textContent = `${pct}% utilizado`;
  if (limitEl) limitEl.textContent = formatCurrency(Math.max(0, CREDIT_LIMIT - state.balance));

  if (parseFloat(pct) > 85) {
    addAlert('danger', 'danger', 'Limite crítico',
      `Você utilizou ${pct}% do seu limite de crédito. Considere um depósito.`);
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

const txLabels = { sent: 'D', received: 'C', deposit: 'C' };

function buildTxItem(tx) {
  const div = document.createElement('div');
  div.className = 'tx-item';
  div.innerHTML = `
    <div class="tx-icon ${tx.type}">${txLabels[tx.type]}</div>
    <div class="tx-info">
      <div class="tx-name">${tx.name}</div>
      <div class="tx-date">${tx.description ? tx.description + ' · ' : ''}${formatDate(tx.date)}</div>
    </div>
    <div class="tx-amount ${tx.type}">
      ${tx.type === 'sent' ? '−' : '+'}${formatCurrency(tx.amount)}
    </div>
  `;
  return div;
}

function renderRecentTransactions() {
  const c = document.getElementById('recentTransactions');
  if (!c) return;
  c.innerHTML = '';
  state.transactions.slice(0, 5).forEach(tx => c.appendChild(buildTxItem(tx)));
}

function renderHistory() {
  const c = document.getElementById('historyTransactions');
  if (!c) return;
  c.innerHTML = '';
  const filtered = state.activeFilter === 'all'
    ? state.transactions
    : state.transactions.filter(tx => tx.type === state.activeFilter);
  if (filtered.length === 0) {
    c.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;padding:16px 0;">Nenhuma movimentação encontrada.</p>';
    return;
  }
  filtered.forEach(tx => c.appendChild(buildTxItem(tx)));
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.activeFilter = btn.dataset.filter;
    renderHistory();
  });
});

function validateTransfer({ recipientName, recipientAccount, amount }) {
  const errors = [];
  if (!recipientName.trim())    errors.push('Informe o nome do favorecido.');
  if (!recipientAccount.trim()) errors.push('Informe a agência e conta do favorecido.');
  if (!amount || isNaN(amount) || amount <= 0) errors.push('Informe um valor válido.');
  if (amount > state.balance)   errors.push(`Saldo insuficiente. Saldo disponível: ${formatCurrency(state.balance)}.`);
  if (amount > 5000)            errors.push('Transferências acima de R$ 5.000,00 requerem autenticação adicional no aplicativo BB.');
  if (recipientAccount === `${state.user.agency} · ${state.user.account}`) errors.push('Não é possível transferir para sua própria conta.');
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

function confirmTransfer() {
  const tx = state.pendingTransfer;
  if (!tx) return;

  state.balance -= tx.amount;

  state.transactions.unshift({
    id: Date.now(),
    type: 'sent',
    name: tx.recipientName,
    description: tx.description || 'Transferência',
    amount: tx.amount,
    date: new Date(),
  });

  renderBalance();
  renderRecentTransactions();
  updateBalanceBar();

  addAlert('success', 'success', 'Transferência realizada',
    `Débito de ${formatCurrency(tx.amount)} para ${tx.recipientName} confirmado.`);

  // Limpa form
  ['recipientName','recipientAccount','transferAmount','transferDesc'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  closeModal('modal-confirm');

  document.getElementById('successMsg').textContent =
    `${formatCurrency(tx.amount)} transferidos para ${tx.recipientName} com sucesso.`;
  document.getElementById('protocolNum').textContent = genProtocol();
  openModal('modal-success');

  state.pendingTransfer = null;
}

function openPixModal() { openModal('modal-pix'); }

function processPix() {
  const key    = document.getElementById('pixKey').value.trim();
  const amount = parseFloat(document.getElementById('pixAmount').value);

  if (!key)              { showToast('Informe a chave Pix do destinatário.'); return; }
  if (!amount || amount <= 0) { showToast('Informe um valor válido.'); return; }
  if (amount > state.balance) { showError(`Saldo insuficiente para este Pix.\nSaldo disponível: ${formatCurrency(state.balance)}`); return; }

  state.balance -= amount;
  state.transactions.unshift({ id: Date.now(), type: 'sent', name: `Pix → ${key}`, description: 'Pix enviado', amount, date: new Date() });

  renderBalance(); renderRecentTransactions(); updateBalanceBar();

  document.getElementById('pixKey').value    = '';
  document.getElementById('pixAmount').value = '';
  closeModal('modal-pix');
  showToast(`Pix de ${formatCurrency(amount)} realizado com sucesso.`);
}

function openDepositModal() { openModal('modal-deposit'); }

function processDeposit() {
  const amount = parseFloat(document.getElementById('depositAmount').value);
  if (!amount || amount <= 0) { showToast('Informe um valor válido.'); return; }

  state.balance += amount;
  state.transactions.unshift({ id: Date.now(), type: 'deposit', name: 'Crédito em conta', description: 'Depósito', amount, date: new Date() });

  renderBalance(); renderRecentTransactions(); updateBalanceBar();
  addAlert('success', 'success', 'Crédito recebido', `${formatCurrency(amount)} creditados na sua conta corrente.`);

  document.getElementById('depositAmount').value = '';
  closeModal('modal-deposit');
  showToast(`Crédito de ${formatCurrency(amount)} realizado com sucesso.`);
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
  badge.textContent = parseInt(badge.textContent || '0') + 1;
}

function dismissAlert(btn) {
  const alert = btn.closest('.alert-item');
  alert.style.opacity   = '0';
  alert.style.transform = 'translateX(8px)';
  alert.style.transition = 'all 0.2s ease';
  setTimeout(() => alert.remove(), 220);

  const badge = document.getElementById('notifBadge');
  badge.textContent = Math.max(0, parseInt(badge.textContent || '0') - 1);
}

function showError(msg) {
  document.getElementById('errorMsg').innerHTML = msg.replace(/\n/g, '<br>');
  openModal('modal-error');
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
  setTimeout(() => alert('Você foi desconectado.\n(Em produção, redirecionaria para o login do BB.)'), 1200);
});

(function init() {
  renderBalance();
  renderRecentTransactions();
  updateBalanceBar();
})();
