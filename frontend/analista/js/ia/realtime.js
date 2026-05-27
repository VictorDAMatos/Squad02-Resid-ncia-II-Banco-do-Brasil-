export function mostrarNotificacao(mensagem) {

    const toast = document.createElement('div');

    toast.className = 'toast-alert';

    toast.innerText = mensagem;

    document.body.appendChild(toast);

    setTimeout(() => {

        toast.remove();

    }, 4000);
}