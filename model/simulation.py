import numpy as np

def monte_carlo_simulation(media, error, n_sim=5000):
    resultados = []
    partidos = list(media.keys())

    for _ in range(n_sim):
        sim = {}
        for p in partidos:
            sim[p] = np.random.normal(media[p], error)
        resultados.append(sim)

    return resultados
