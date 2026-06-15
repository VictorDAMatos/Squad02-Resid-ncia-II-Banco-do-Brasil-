import pandas as pd

def carregar_dados(path):
    df = pd.read_json(path)

    df["horario"] = pd.to_datetime(df["data"]).dt.hour

    return df