import numpy as np

def fragmentacion(escanos_dict):
    total = sum(escanos_dict.values())
    proporciones = [v/total for v in escanos_dict.values()]
    return 1 / sum(p**2 for p in proporciones)

def volatilidad(historial):
    return np.std(historial)
