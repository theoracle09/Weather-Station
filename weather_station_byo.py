from gpiozero import Button
import time
import math
import statistics
import bme280_sensor
import wind_direction_byo
import ds18b20_therm
import database
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Constant variable definition
CM_IN_A_KM = 100000.0
SECS_IN_A_HOUR = 3600
BUCKET_SIZE = 0.2794     # Volume of rain required to tip rain meter one time

# Initialize ground temp probe
temp_probe = ds18b20_therm.DS18B20()

# Define wind speed and direction lists
store_speeds = []
store_directions = []

# Define variables
wind_count = 0           # Counts how many half-rotations
radius_cm = 9.0          # Radius of anemometer
wind_interval = 5        # How many secs to collect wind dir and speed
interval = 5             # Data collection interval in secs. 5 mins = 5 * 60 = 300
rain_count = 0           # Counts rain bucket tips

#Connect to MQTT
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("192.168.1.16", 1883)

# Every half-rotation, add 1 to count
def spin():
    global wind_count
    wind_count = wind_count + 1

# Calculate the wind speed
def calculate_speed(time_sec):
    global wind_count
    circumference_cm = (2 * math.pi) * radius_cm
    rotations = wind_count / 2.0

    # Calculate distance travelled by a cup in cm
    dist_km = (circumference_cm * rotations) / CM_IN_A_KM
    
    km_per_sec = dist_km / time_sec
    km_per_hour = 1.18 * (km_per_sec * SECS_IN_A_HOUR) # Multiply wind speed by 'anemometer factor'

    return km_per_hour

# Convert C to F
def celsius_to_f(temp_c):
    f = (temp_c * 9/5) + 32
    return f

# Reset functions
def reset_wind():
    global wind_count
    wind_count = 0

def bucket_tipped():
    global rain_count
    rain_count = rain_count + 1

def reset_rainfall():
    global rain_count
    rain_count = 0

rain_sensor = Button(6)
rain_sensor.when_activated = bucket_tipped

wind_speed_sensor = Button(5)
wind_speed_sensor.when_activated = spin

# Define database
#db = database.weather_database()

# Main loop
while True:
    start_time = time.time()
    while time.time() - start_time <= interval:
        wind_start_time = time.time()
        reset_wind()
        while time.time() - wind_start_time <= wind_interval:
            store_directions.append(wind_direction_byo.get_value())
        
        final_speed = calculate_speed(wind_interval)
        store_speeds.append(final_speed)

    wind_speed = round(statistics.mean(store_speeds), 1)
    wind_gust = round(max(store_speeds), 1)
    rainfall = rain_count * BUCKET_SIZE
    wind_direction = wind_direction_byo.get_average(store_directions)
    ground_temp = temp_probe.read_temp()
    
    humidity, pressure, ambient_temp = bme280_sensor.read_all()

    # Round wind_direction, humidity, pressure, ambient_temp, ground_temp, and rainfall to 1 decimals 
    # and convert C readings to F
    wind_direction = round(wind_direction)
    humidity = round(humidity, 1)
    pressure = round(pressure, 1)
    ambient_temp = celsius_to_f(round(ambient_temp, 1))
    ground_temp = celsius_to_f(round(ground_temp, 1))
    rainfall = round(rainfall, 1)
    
    # Record current date and time
    now = datetime.now()

    # dd/mm/YY H:M:S
    last_message = now.strftime("%m/%d/%Y %H:%M:%S")

    print(last_message, wind_speed, wind_gust, rainfall, wind_direction, humidity, pressure, ambient_temp, ground_temp)

    # Create JSON dict for MQTT transmission
    send_msg = {
        'wind_speed': wind_speed,
        'wind_gust': wind_gust,
        'rainfall': rainfall,
        'wind_direction': wind_direction,
        'humidity': humidity,
        'pressure': pressure,
        'ambient_temp': ambient_temp,
        'ground_temp': ground_temp,
        'last_message': last_message
    }

    # Convert message to json
    payload = json.dumps(send_msg)

    # Publish to mqtt
    client.publish("raspberry/ws/sensors", payload, qos=0)

    # Record to database
    #db.insert(ambient_temp, ground_temp, 0, pressure, humidity, wind_direction, wind_speed, wind_gust, rainfall)

    # Reset wind speed list, wind direction list, and rainfall max
    store_speeds = []
    store_directions = []
    reset_rainfall()
    
