import numpy as np
from collections import deque

class AtlasTwin:
    def __init__(self):
        self.temp_hist = deque(maxlen=100)
        self.press_hist = deque(maxlen=100)

        self.beta = 0.3
        self.comp_temp = 0
        self.pred_temp = 0

        self.state = "INIT"
        self.health = "GOOD"

    def update(self, d):
        t = d["temp"]
        ext = d.get("ext_temp", t)

        # ---------- Adaptive Correction ----------
        error = ext - t
        self.beta += 0.0005 * error
        self.beta = float(np.clip(self.beta, 0.1, 0.5))

        self.comp_temp = t + self.beta * error

        # ---------- History ----------
        self.temp_hist.append(self.comp_temp)
        self.press_hist.append(d["pressure"])

        # ---------- Features ----------
        temp_rate = self.temp_hist[-1] - self.temp_hist[-2] if len(self.temp_hist) > 1 else 0
        pressure_rate = self.press_hist[-1] - self.press_hist[-2] if len(self.press_hist) > 1 else 0

        # ---------- Prediction ----------
        self.pred_temp = self.comp_temp + temp_rate * 5 if len(self.temp_hist) > 5 else self.comp_temp

        # ---------- Smoothed ----------
        temp_smooth = np.mean(self.temp_hist)
        pressure_smooth = np.mean(self.press_hist)

        # ---------- State ----------
        anomaly_score = abs(error) + abs(temp_rate) * 2

        if anomaly_score > 10:
            self.state = "ANOMALY"
        elif self.pred_temp > 35:
            self.state = "HEAT_RISK"
        elif pressure_rate < -0.5:
            self.state = "STORM_RISK"
        else:
            self.state = "NORMAL"

        # ---------- Health ----------
        if len(self.temp_hist) > 20:
            if max(self.temp_hist) - min(self.temp_hist) < 0.05:
                self.health = "STUCK"
            else:
                self.health = "GOOD"

        return {
            **d,
            "comp_temp": self.comp_temp,
            "temp_smooth": temp_smooth,
            "pressure_smooth": pressure_smooth,
            "beta": self.beta,
            "state": self.state,
            "health": self.health,
            "pred_temp": self.pred_temp,
            "temp_rate": temp_rate,
            "pressure_rate": pressure_rate,
            "anomaly_score": anomaly_score
        }