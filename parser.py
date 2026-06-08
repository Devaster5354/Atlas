def parse_data(line):
    try:
        parts = line.split(",")

        if len(parts) != 8:
            return None

        return {
            "temp": float(parts[0]),
            "pressure": float(parts[1]),
            "aq": float(parts[2]),
            "ext_temp": float(parts[3]),
            "ext_hum": float(parts[4]),
            "ext_press": float(parts[5]),
            "alt": float(parts[6]),
            "cond": int(parts[7])
        }

    except:
        return None