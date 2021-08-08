# Raspberry Pi Weather Station with MQTT

## TODO

- Make feature list / section
- Make future features list / section (if any)

## About

This project takes the [offical Raspberry Pi Weather Station](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station) and removes all the extra files dealing with Oracle. Instead of uploading to a web server, this broadcasts sensor data as a JSON object via MQTT to my home assistant installation.

## Feature List

- Local pressure
- Local humidity
- local temperature
- local rainfall in inches
- local wind direction
- local wind speed
- local wind gust (calculated in Home Assistant)
- local hourly, daily, and weekly rainfall (calculated in Home Assistant)

## Hardware List

See the [offical Raspberry Pi Weather Station - What You Will Need](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station/1) section for hardware needed. Here's what I used:

- Raspberry Pi 4 8GB Model B
- BME280 pressure, temperature, and humidity sensor
- DS18B20 digital thermal probe
- [Anemometer, wind vane, and rain gauge](https://www.argentdata.com/catalog/product_info.php?products_id=145)
- 12' of 25 conductor cable for connection between sensor array and raspi box. [Something like this](https://www.amazon.com/gp/product/B00B88BFKC/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1)

I also used this 3D printed [radiation shield](https://www.thingiverse.com/thing:1067700) for the BME280 sensor.

## Running Script When Pi Starts

These were the steps I had to take so the weather station script will run on boot. SSH into your raspberry pi and type the following to create a new system service:

```
sudo nano /etc/systemd/system/weatherstation.service
```

Paste this into the new file:

```sh
[Unit]
Description=Weather Station Service
Wants=systemd-networkd-wait-online.service
After=systemd-networkd-wait-online.service

[Service]
Type=simple
ExecStartPre=/bin/sh -c 'until ping -c1 google.com; do sleep 1; done;'
ExecStart=/usr/bin/python3 /home/pi/weather-station/weather_station_byo.py > /home/pi/weather-station/logs/log.txt 2>$1

[Install]
WantedBy=multi-user.target
```

Systemd needs to be made aware of the configuration change. Reload the systemd daemon with the following:

```
sudo systemctl daemon-reload
```

Enable the new weatherstation service:

```
sudo systemctl enable weatherstation.service
```

The systemd-networkd-wait-online service needs to be enabled. Type this next:

```
sudo systemctl enable systemd-networkd-wait-online.service
```

Restart the pi and once the network services are loaded, the script should run and start broadcasting sensor data over MQTT. If it doesn't, type in this command to see the status of the service and diagnose from there.

```
sudo systemctl status weatherstation.service
```