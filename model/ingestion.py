import pandas as pd

def load_polls(path="data/encuestas.csv"):
    df = pd.read_csv(path, parse_dates=["fecha"])
    return df.sort_values("fecha")
