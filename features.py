import numpy as np

def compute_features(data, history):
    temps = history["temp"]
    pressures = history["pressure"]

    features = {}

    # --- moving averages ---
    if len(temps) > 5:
        features["temp_ma"] = np.mean(temps[-5:])
    else:
        features["temp_ma"] = data["temp"]

    # --- rate of change ---
    if len(temps) > 1:
        features["temp_rate"] = temps[-1] - temps[-2]
    else:
        features["temp_rate"] = 0

    if len(pressures) > 1:
        features["pressure_rate"] = pressures[-1] - pressures[-2]
    else:
        features["pressure_rate"] = 0

    return features