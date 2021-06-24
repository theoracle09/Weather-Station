def voltage_divider(r1, r2, vin):
    vout = (vin * r1) / (r1 + r2)

    return round(vout, 3)

print(voltage_divider(33000, 10000, 5.0))