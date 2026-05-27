import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomaliaService:
    def __init__(self):
        self.modelo = IsolationForest(contamination=0.02, random_state=42)  # 2% de rigor
        self.scaler = StandardScaler()  # Para normalizar os dados
        self.modelo_treinado = False

    def treinar_modelo(self, dados_historicos: list[dict]):
        if not dados_historicos: return False

        df = pd.DataFrame(dados_historicos)
        # Variáveis: valor, hora, frequencia, e 'score_credito' (exemplo de nova variável)
        features = df[['valor', 'hora_numerica', 'frequencia']]

        # Normaliza os dados (deixa tudo na mesma escala de -1 a 1)
        self.scaler.fit(features)
        features_scaled = self.scaler.transform(features)

        self.modelo.fit(features_scaled)
        self.modelo_treinado = True
        return True

    def classificar_risco(self, valor: float, hora_numerica: float, frequencia: int) -> dict:
        if not self.modelo_treinado:
            return {"erro": "IA não treinada."}

        # Prepara e Normaliza a entrada
        entrada = pd.DataFrame([{'valor': valor, 'hora_numerica': hora_numerica, 'frequencia': frequencia}])
        entrada_scaled = self.scaler.transform(entrada)

        # decision_function retorna a distância do "cluster" normal
        score = self.modelo.decision_function(entrada_scaled)[0]

        # Lógica de Risco BB (Ultra Precisa)
        if score > 0.10:
            nivel, status = 1, "Aprovada"
        elif 0.00 <= score <= 0.10:
            nivel, status = 2, "Em Análise Manutenção"
        else:
            nivel, status = 3, "Bloqueio Imediato"

        return {
            "score_ia": round(float(score), 4),
            "nivel_risco": nivel,
            "status": status,
            "confianca": f"{round((0.5 - score) * 100, 2)}%"  # Cálculo de confiança na fraude
        }