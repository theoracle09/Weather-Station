from typing import Counter
from gpiozero import Button

BUCKET_SIZE = 0.2794

rain_sensor = Button(6)
count = 0

def bucket_tipped():
    global count
    count += 1
    print(count * BUCKET_SIZE)

def reset_rainfall():
    global count
    count = 0

while True:
    rain_sensor.when_activated = bucket_tipped