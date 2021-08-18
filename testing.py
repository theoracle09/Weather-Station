import paho.mqtt.client as mqtt
import time

flag_connected = 0

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
client.connect("192.168.1.16", 1883) 

if __name__ == '__main__':

    client.loop_start()

    while flag_connected == 0:
        print("Not connected. Waiting 1 second.")
        time.sleep(1)

    print("Connection successful...")

    try:
        for i in range(25):
            # the four parameters are topic, sending content, QoS and whether retaining the message respectively
            client.publish('raspberry/topic', payload=i, qos=0, retain=False)
            print(f"send {i} to raspberry/topic")
            time.sleep(1)
    except KeyboardInterrupt:
        print("User exited program.")
        pass


    client.loop_stop()
    print("Loop Stopped.")
    client.disconnect()
    print("MQTT Disconnected.")
