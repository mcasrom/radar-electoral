import numpy as np
from datetime import datetime

def compute_weights(df):
    hoy = datetime.today()
    df = df.copy()
    df["antiguedad"] = (hoy - df["fecha"]).dt.days

    peso_muestra = np.sqrt(df["muestra"])
    peso_tiempo = 1 / (1 + df["antiguedad"] / 30)

    df["peso"] = peso_muestra * peso_tiempo
    return df

def weighted_average(df, partidos):
    resultados = {}
    for p in partidos:
        resultados[p] = np.average(df[p], weights=df["peso"])
    return resultados
