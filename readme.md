# Raspberry Pi Weather Station with MQTT

## TODO

- Make feature list / section
- Make hardware list / section
- Make future features list / section (if any)

## About

This project takes the [offical Raspberry Pi Weather Station](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station) and removes the files I didn't need to make it run with Home Assistant.

## Running Script When Pi Starts

Create new system service

```console
pi@raspberrypi:~ $ sudo nano /etc/systemd/system/weatherstation.service
```


```
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