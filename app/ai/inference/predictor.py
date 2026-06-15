from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import unicodedata

import joblib
import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"

model = joblib.load(MODELS_DIR / "isolation_forest.pkl")
scaler = joblib.load(MODELS_DIR / "scaler.pkl")

encoder_tipo = joblib.load(MODELS_DIR / "encoder_tipo.pkl")
encoder_dispositivo = joblib.load(MODELS_DIR / "encoder_dispositivo.pkl")
encoder_cidade = joblib.load(MODELS_DIR / "encoder_cidade.pkl")
encoder_dia_semana = joblib.load(MODELS_DIR / "encoder_dia_semana.pkl")
encoder_estado = joblib.load(MODELS_DIR / "encoder_estado.pkl")
encoder_pais = joblib.load(MODELS_DIR / "encoder_pais.pkl")
encoder_categoria = joblib.load(MODELS_DIR / "encoder_categoria.pkl")


def _sem_acento(valor: Any) -> str:
    texto = str(valor or "").strip()
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def _normalizar_token(valor: Any) -> str:
    texto = _sem_acento(valor).lower().strip()
    texto = texto.replace(" ", "_").replace("-", "_")
    aliases = {
        "caixa_eletronico": "caixa_eletronico",
        "caixa_eletronico_24h": "caixa_eletronico",
        "caixa_eletronico_bb": "caixa_eletronico",
        "cartao_credito": "credito",
        "cartao_de_credito": "credito",
        "cartao_debito": "debito",
        "cartao_de_debito": "debito",
        "transferencia": "transferencia",
        "transferencia_bancaria": "transferencia",
        "pix": "pix",
        "internet_banking": "web",
        "frontend_usuario": "web",
        "pix_frontend_usuario": "app_mobile",
    }
    return aliases.get(texto, texto)


def _normalizar_cidade(valor: Any) -> str:
    texto_original = str(valor or "").strip()
    texto_sem_acento = _sem_acento(texto_original)
    classes = {str(c).lower(): str(c) for c in encoder_cidade.classes_}
    return classes.get(texto_sem_acento.lower(), texto_original or "Recife")


def _normalizar_estado(valor: Any) -> str:
    texto = _sem_acento(valor).upper().strip()
    return texto if texto in set(encoder_estado.classes_) else "PE"


def _normalizar_pais(valor: Any) -> str:
    texto = str(valor or "Brasil").strip()
    classes = {str(c).lower(): str(c) for c in encoder_pais.classes_}
    return classes.get(_sem_acento(texto).lower(), "Brasil")


def _normalizar_dia_semana(valor: Any, data: pd.Timestamp) -> str:
    texto = str(valor or "").strip()
    classes = {str(c).lower(): str(c) for c in encoder_dia_semana.classes_}
    if texto.lower() in classes:
        return classes[texto.lower()]
    return data.day_name()


def _parse_data(transacao: dict[str, Any]) -> pd.Timestamp:
    data = str(transacao.get("data") or datetime.now().date())
    hora = str(transacao.get("hora") or "00:00")
    texto = data if "T" in data or " " in data else f"{data} {hora}"
    timestamp = pd.to_datetime(texto, errors="coerce")
    if pd.isna(timestamp):
        return pd.Timestamp.now()
    return timestamp


def safe_transform(encoder: Any, value: Any) -> int:
    try:
        return int(encoder.transform([value])[0])
    except Exception:
        return 0


def prever(transacao: dict[str, Any]) -> dict[str, Any]:
    """Executa a inferência do Isolation Forest para uma transação.

    Mantém compatibilidade com o projeto antigo, mas aceita também os campos do
    projeto avançado. Campos não enviados recebem valores seguros para que o
    frontend atual continue funcionando sem precisar refazer a interface.
    """
    data = _parse_data(transacao)

    tipo_transacao = safe_transform(encoder_tipo, _normalizar_token(transacao.get("tipo_transacao", "pix")))
    dispositivo = safe_transform(encoder_dispositivo, _normalizar_token(transacao.get("dispositivo", "web")))
    cidade = safe_transform(encoder_cidade, _normalizar_cidade(transacao.get("cidade", "Recife")))
    dia_semana_valor = _normalizar_dia_semana(transacao.get("dia_semana"), data)
    dia_semana = safe_transform(encoder_dia_semana, dia_semana_valor)

    # Mantidos para compatibilidade/documentação do pipeline original.
    safe_transform(encoder_estado, _normalizar_estado(transacao.get("estado", "PE")))
    safe_transform(encoder_pais, _normalizar_pais(transacao.get("pais", "Brasil")))
    safe_transform(encoder_categoria, _normalizar_token(transacao.get("categoria", "servicos")))

    dados = pd.DataFrame([{
        "valor": float(transacao.get("valor") or 0),
        "horario": int(data.hour),
        "dia_semana": dia_semana,
        "latitude": float(transacao.get("latitude") or 0),
        "longitude": float(transacao.get("longitude") or 0),
        "tentativas": int(transacao.get("tentativas") or 1),
        "tipo_transacao": tipo_transacao,
        "dispositivo": dispositivo,
        "cidade": cidade,
        "mes": int(data.month),
        "dia": int(data.day),
    }])

    dados_normalizados = scaler.transform(dados)
    pred = model.predict(dados_normalizados)
    score = float(model.decision_function(dados_normalizados)[0])

    risco = 1
    valor = float(transacao.get("valor") or 0)
    tentativas = int(transacao.get("tentativas") or 1)

    # Ajuste da US05/US06: o modelo define a anomalia, mas a severidade final
    # considera valor e tentativas para separar suspeita progressiva de bloqueio crítico.
    if valor > 10000 and (pred[0] == -1 or score < 0.05 or tentativas >= 5):
        risco = 3
    elif pred[0] == -1 or score < 0.05 or tentativas >= 5:
        risco = 2

    motivo = "Comportamento normal"
    if risco == 2:
        motivo = "Comportamento suspeito detectado pela IA"
    elif risco == 3:
        motivo = "Forte indício de fraude detectado pela IA"

    return {
        "anomalia": bool(pred[0] == -1),
        "score": score,
        "risco": int(risco),
        "motivo": motivo,
    }
