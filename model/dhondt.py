import pandas as pd

def dhondt(votos, escanos):
    validos = {p: v for p, v in votos.items() if v >= 3}
    lista = []
    for p, v in validos.items():
        for i in range(1, escanos + 1):
            lista.append((p, v / i))
    df = pd.DataFrame(lista, columns=["partido","cociente"])
    df = df.sort_values("cociente", ascending=False)
    return df.head(escanos)["partido"].value_counts().to_dict()
