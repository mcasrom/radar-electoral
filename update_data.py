#!/usr/bin/env python3
import pandas as pd
import datetime
import random
import os

DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "votos_historicos.csv")
os.makedirs(DATA_DIR, exist_ok=True)

PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]

start_date = datetime.date.today() - datetime.timedelta(weeks=12)
registros = []

for semana in range(12):
    fecha = start_date + datetime.timedelta(weeks=semana)
    for partido in PARTIDOS:
        if partido=="PP": voto = round(random.uniform(28,35),2)
        elif partido=="PSOE": voto = round(random.uniform(24,30),2)
        elif partido=="VOX": voto = round(random.uniform(14,18),2)
        elif partido=="SUMAR": voto = round(random.uniform(7,10),2)
        else: voto = round(random.uniform(0,5),2)
        fiabilidad = round(random.uniform(0.7,0.95),2)
        registros.append({
            "fecha": fecha,
            "partido": partido,
            "voto": voto,
            "fuente": "SeedSim",
            "fiabilidad": fiabilidad
        })

df = pd.DataFrame(registros)
df.to_csv(CSV_FILE, index=False)
print(f"📊 CSV generado correctamente: {CSV_FILE} — {len(df)} registros")
