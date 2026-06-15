import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder

# =========================
# CARREGAR DADOS
# =========================

df = pd.read_json("transacoes_treino.json")

# =========================
# FEATURES TEMPORAIS
# =========================

# Converter data
df["data"] = pd.to_datetime(df["data"])

# Criar features temporais
df["horario"] = df["data"].dt.hour
df["mes"] = df["data"].dt.month
df["dia"] = df["data"].dt.day
df["dia_mes"] = df["data"].dt.day

# =========================
# ENCODERS
# =========================

encoder_tipo = LabelEncoder()
encoder_dispositivo = LabelEncoder()
encoder_cidade = LabelEncoder()
encoder_dia_semana = LabelEncoder()
encoder_estado = LabelEncoder()
encoder_pais = LabelEncoder()
encoder_categoria = LabelEncoder()

df["tipo_transacao"] = encoder_tipo.fit_transform(df["tipo_transacao"])
df["dispositivo"] = encoder_dispositivo.fit_transform(df["dispositivo"])
df["cidade"] = encoder_cidade.fit_transform(df["cidade"])
df["dia_semana"] = encoder_dia_semana.fit_transform(df["dia_semana"])
df["estado"] = encoder_estado.fit_transform(df["estado"])
df["pais"] = encoder_pais.fit_transform(df["pais"])
df["categoria"] = encoder_categoria.fit_transform(df["categoria"])

# =========================
# FEATURES USADAS PELA IA
# =========================

features = [
    "valor",
    "horario",
    "dia_semana",
    "latitude",
    "longitude",
    "tentativas",
    "tipo_transacao",
    "dispositivo",
    "cidade",
    "mes",
    "dia"
]

X = df[features]

# =========================
# NORMALIZAÇÃO
# =========================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

# =========================
# MODELO
# =========================

model = IsolationForest(
    n_estimators=300,
    contamination=0.02,
    random_state=42
)

model.fit(X_scaled)

# SALVAR MODELO

joblib.dump(model, "app/ai/models/isolation_forest.pkl")
joblib.dump(scaler, "app/ai/models/scaler.pkl")

# Encoders

joblib.dump(encoder_tipo, "app/ai/models/encoder_tipo.pkl")
joblib.dump(encoder_dispositivo, "app/ai/models/encoder_dispositivo.pkl")
joblib.dump(encoder_cidade, "app/ai/models/encoder_cidade.pkl")

joblib.dump(encoder_dia_semana, "app/ai/models/encoder_dia_semana.pkl")
joblib.dump(encoder_estado, "app/ai/models/encoder_estado.pkl")
joblib.dump(encoder_pais, "app/ai/models/encoder_pais.pkl")
joblib.dump(encoder_categoria, "app/ai/models/encoder_categoria.pkl")

print("IA treinada com sucesso!")