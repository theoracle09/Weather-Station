# Raspberry Pi Weather Station with MQTT

## TODO

- Make feature list / section
- Make hardware list / section
- Make future features list / section (if any)

## About

This project takes the [offical Raspberry Pi Weather Station](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station) and removes all the extra files dealing with Oracle. Instead of uploading to a web server, this broadcasts sensor data as a JSON object via MQTT to my home assistant installation.

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