export async function getDashboardIA() {

    const response =
        await fetch("/ia/dashboard");

    return await response.json();
}

export async function getTransacoes() {

    const response =
        await fetch("/transacoes/");

    return await response.json();
}