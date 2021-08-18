from gpiozero import Button
from gpiozero import CPUTemperature
import time
import math
import statistics
import bme280_sensor
import wind_direction_byo
import ds18b20_therm
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Global variable definition
flag_connected = 0      # Loop flag for waiting to connect to MQTT broker

# Constant variable definition
MQTT_HOST = "192.168.1.16"
MQTT_PORT = 1883
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
    print("Connected with flags [%s] rtn code [%d]"% (flags, rc) )
    global flag_connected
    flag_connected = 1

def on_disconnect(client, userdata, rc):
    print("disconnected with rtn code [%d]"% (rc) )
    global flag_connected
    flag_connected = 0

client = mqtt.Client("WX")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect(MQTT_HOST, MQTT_PORT) 

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

    # Convert KMH to MPH
    mph = 0.6214 * km_per_hour

    return mph

# Convert C to F
def celsius_to_f(temp_c):
    f = (temp_c * 9/5) + 32
    return f

# Convert mm to inches
def mm2inches(mm):
    inches = mm * 0.0393701
    inches = round(inches,4)
    return inches

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

# Read CPU temp for future fan logic
cpu = CPUTemperature()

# Main loop
if __name__ == '__main__':

    client.loop_start()

    # Wait to receive the connected callback for MQTT
    while flag_connected == 0:
        print("Not connected. Waiting 1 second.")
        time.sleep(1)

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
        rainfall = mm2inches(rainfall)

        cpu_temp = celsius_to_f(round(cpu.temperature, 1))
        
        # Record current date and time for message timestamp
        now = datetime.now()

        # Format message timestamp to mm/dd/YY H:M:S
        last_message = now.strftime("%m/%d/%Y %H:%M:%S")

        # Debugging (used when testing and need to print variables)
        #print(last_message, wind_speed, rainfall, wind_direction, humidity, pressure, ambient_temp, ground_temp)

        # Create JSON dict for MQTT transmission
        send_msg = {
            'wind_speed': wind_speed,
            'rainfall': rainfall,
            'wind_direction': wind_direction,
            'humidity': humidity,
            'pressure': pressure,
            'ambient_temp': ambient_temp,
            'ground_temp': ground_temp,
            'last_message': last_message,
            'cpu_temp': cpu_temp
        }

        # Convert message to json
        payload = json.dumps(send_msg)

        # Publish to mqtt
        client.publish("raspberry/ws/sensors", payload, qos=0)

        # Reset wind speed list, wind direction list, and rainfall max
        store_speeds = []
        store_directions = []
        reset_rainfall()
    
    client.loop_stop()
    print("Loop Stopped.")
    client.disconnect()
    print("MQTT Disconnected.")
