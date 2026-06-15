def calcular_risco(score, valor):
    
    if score < -0.25 and valor > 10000:
        return 3

    if score < -0.10:
        return 2

    return 1