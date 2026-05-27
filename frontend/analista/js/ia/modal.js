export function abrirModal(transacao) {

    const modal = document.getElementById(
        'modalIA'
    );

    if (!modal) return;

    modal.style.display = 'flex';

    document.getElementById(
        'modalContent'
    ).innerHTML = `
        <h2>Análise IA</h2>

        <p><strong>ID:</strong> ${transacao.id}</p>

        <p><strong>Conta:</strong> ${transacao.conta}</p>

        <p><strong>Valor:</strong> R$ ${transacao.valor}</p>

        <p><strong>Cidade:</strong> ${transacao.cidade}</p>

        <p><strong>Risco:</strong> ${transacao.classificacao_risco}</p>
    `;
}