from app.ai.inference.predictor import prever

transacao = {
    "valor": 25000,
    "data": "2026-05-26",
    "dia_semana": "Tuesday",
    "latitude": -10.9472,
    "longitude": -37.0731,
    "tentativas": 7,
    "tipo_transacao": "PIX",
    "dispositivo": "Android",
    "cidade": "Aracaju",
    "estado": "SE",
    "pais": "Brasil",
    "categoria": "Transferencia"
}

resultado = prever(transacao)

print(resultado)