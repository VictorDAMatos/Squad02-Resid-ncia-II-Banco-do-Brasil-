// Função que "conversa" com o FastAPI
async function buscarExtrato() {
    try {
        // Faz a requisição (GET) para a sua rota de transações
        const resposta = await fetch('http://127.0.0.1:8000/transactions/');
        const transacoes = await resposta.json();
        
        const lista = document.getElementById('lista-transacoes');
        lista.innerHTML = ''; // Limpa a lista antes de mostrar os novos
        
        // Para cada transação encontrada, cria um item na lista
        transacoes.forEach(t => {
            const item = document.createElement('li');
            item.innerHTML = `<strong>€ ${t.valor}</strong> - ${t.categoria} (em ${t.data})`;
            lista.appendChild(item);
        });

    } catch (erro) {
        console.error("Erro ao buscar a API:", erro);
        alert("Erro de conexão! O Uvicorn está rodando?");
    }
}