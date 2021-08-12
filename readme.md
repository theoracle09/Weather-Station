# Raspberry Pi Weather Station with MQTT

## TODO

- Make future features list / section (if any)

## About

This project takes the [offical Raspberry Pi Weather Station](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station) and removes all the extra files dealing with Oracle, along with some new features. The raspi broadcasts the sensor data as a JSON dict over MQTT and is displayed in a [Home Assistant](https://www.home-assistant.io/) dashboard.

**NOTE:** As of now I am broadcasting on MQTT every 5 seconds and taking wind measurements every 5 seconds. Because of this, I removed the wind gust measurements from the original project, as I'm calculating this from Home Assistant.

## Feature List

The following sensors are broadcast as a JSON dict over MQTT, and displayed in a Home Assistant dashboard:

- Local pressure
- Local humidity
- Local temperature
- Local rainfall in inches
- Local wind direction
- Local wind speed
- Local wind gust (calculated in Home Assistant)
- Local hourly, daily, and weekly rainfall (calculated in Home Assistant)

Home Assistant uses the [utitilty meter integration](https://www.home-assistant.io/integrations/utility_meter/) to track hourly, daily, and weekly rainfall. Node Red saves the max daily wind speed as wind gust to a local file so as to be persistent over Home Assistant restarts. Node Red resets the max daily wind gust every day at midnight. 

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

**NOTICE:** This program uses python3, so it's explicitly called within the ExecStart command. Also note the absolute file path to the weather station main program, along with absolute path to any error log output.

TODO: The ExecStartPre command is executed because the service consistently started before the network services were active and made the program error out and fail. Having the service require a single ping out before startup ensures the pi is indeed connected to the internet before it attempts to connect via MQTT. This will most likely be changed in the future because the connection error needs to be handled at the program level, not the service level. I also don't want to rely on it connecting outside of the local network, so it should check MQTT connection status before moving to main program loop as opposed to dialing outside the network.

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