def generar_narrativa(fragmentacion_indice):
    if fragmentacion_indice > 5:
        return "Alta fragmentación parlamentaria. Escenario de negociación compleja."
    elif fragmentacion_indice > 3:
        return "Fragmentación moderada. Posibles pactos estructurados."
    else:
        return "Sistema relativamente concentrado."
