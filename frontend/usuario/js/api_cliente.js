let transacoesCarregadas = [];

async function buscarExtrato() {
    try {
        const resposta = await fetch('http://127.0.0.1:8000/transacoes/');

        if (!resposta.ok) {
            throw new Error('Erro ao buscar transações');
        }

        const transacoes = await resposta.json();
        transacoesCarregadas = transacoes.map(normalizarTransacao);

        renderizarTransacoes(transacoesCarregadas);
        atualizarBotaoExportar();
    } catch (erro) {
        console.error("Erro ao buscar a API:", erro);
        alert("Erro de conexão! O Uvicorn está rodando?");
    }
}

function normalizarTransacao(transacao) {
    if (!Array.isArray(transacao)) {
        return transacao;
    }

    return {
        id: transacao[0],
        valor: transacao[1],
        data: transacao[2],
        hora: transacao[3],
        categoria: transacao[4],
        conta: transacao[5],
        cidade: transacao[6],
        tipo_transacao: transacao[7],
        dispositivo: transacao[8],
    };
}

function renderizarTransacoes(transacoes) {
    const lista = document.getElementById('lista-transacoes');
    lista.innerHTML = '';

    transacoes.forEach(t => {
        const item = document.createElement('li');
        item.textContent = formatarTransacao(t);
        lista.appendChild(item);
    });
}

function formatarTransacao(transacao) {
    return `${formatarValor(transacao.valor)} - ${transacao.categoria} - ${transacao.data} ${transacao.hora} - Conta ${transacao.conta}`;
}

function formatarValor(valorTransacao) {
    const valor = Number(valorTransacao).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });

    return valor;
}

function formatarTransacaoParaExportacao(transacao) {
    return [
        `Valor: ${formatarValor(transacao.valor)}`,
        `Categoria: ${transacao.categoria}`,
        `Data: ${transacao.data}`,
        `Hora: ${transacao.hora}`,
        `Conta: ${transacao.conta}`,
        `Cidade: ${transacao.cidade}`,
        `Tipo: ${transacao.tipo_transacao}`,
        `Dispositivo: ${transacao.dispositivo}`
    ].join(' | ');
}

function atualizarBotaoExportar() {
    const botaoExportar = document.getElementById('btn-exportar');
    botaoExportar.disabled = transacoesCarregadas.length === 0;
}

function exportarTransacoes() {
    if (transacoesCarregadas.length === 0) {
        alert("Busque as transações antes de exportar.");
        return;
    }

    const conteudo = transacoesCarregadas
        .map((transacao, indice) => `${indice + 1}. ${formatarTransacaoParaExportacao(transacao)}`)
        .join('\n');

    const arquivo = new Blob([conteudo], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(arquivo);
    const link = document.createElement('a');

    link.href = url;
    link.download = 'lista-transacoes.txt';
    link.click();

    URL.revokeObjectURL(url);
}
