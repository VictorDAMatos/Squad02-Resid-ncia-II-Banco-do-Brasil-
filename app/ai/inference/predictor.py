import joblib
import numpy as np
import pandas as pd

model = joblib.load("app/ai/models/isolation_forest.pkl")
scaler = joblib.load("app/ai/models/scaler.pkl")

encoder_tipo = joblib.load("app/ai/models/encoder_tipo.pkl")
encoder_dispositivo = joblib.load("app/ai/models/encoder_dispositivo.pkl")
encoder_cidade = joblib.load("app/ai/models/encoder_cidade.pkl")
encoder_dia_semana = joblib.load("app/ai/models/encoder_dia_semana.pkl")
encoder_estado = joblib.load("app/ai/models/encoder_estado.pkl")
encoder_pais = joblib.load("app/ai/models/encoder_pais.pkl")
encoder_categoria = joblib.load("app/ai/models/encoder_categoria.pkl")

# FUNÇÃO AUXILIAR

def safe_transform(encoder, value):

    try:
        return encoder.transform([value])[0]
    except:
        return 0

def prever(transacao):

    # PROCESSAR DATA

    data = pd.to_datetime(transacao["data"])

    horario = data.hour
    mes = data.month
    dia = data.day

    # ENCODERS

    tipo_transacao = safe_transform(
        encoder_tipo,
        transacao["tipo_transacao"]
    )

    dispositivo = safe_transform(
        encoder_dispositivo,
        transacao["dispositivo"]
    )

    cidade = safe_transform(
        encoder_cidade,
        transacao["cidade"]
    )

    dia_semana = safe_transform(
        encoder_dia_semana,
        transacao["dia_semana"]
    )

    estado = safe_transform(
        encoder_estado,
        transacao["estado"]
    )

    pais = safe_transform(
        encoder_pais,
        transacao["pais"]
    )

    categoria = safe_transform(
        encoder_categoria,
        transacao["categoria"]
    )

    # VETOR IA

    dados = np.array([[
        transacao["valor"],
        horario,
        dia_semana,
        transacao["latitude"],
        transacao["longitude"],
        transacao["tentativas"],
        tipo_transacao,
        dispositivo,
        cidade,
        mes,
        dia
    ]])

    # NORMALIZAÇÃO

    dados = scaler.transform(dados)

    # PREVISÃO

    pred = model.predict(dados)
    score = model.decision_function(dados)[0]

    # CLASSIFICAÇÃO DE RISCO

    risco = 1

    if score < -0.25 and transacao["valor"] > 10000:
        risco = 3

    elif score < -0.10:
        risco = 2

    # EXPLICAÇÃO

    motivo = "Comportamento normal"

    if risco == 2:
        motivo = "Comportamento suspeito detectado"

    if risco == 3:
        motivo = "Forte indício de fraude"

    # RESPOSTA

    return {
    "anomalia": bool(pred[0] == -1),
    "score": float(score),
    "risco": int(risco),
    "motivo": str(motivo)
}