import os
import time
import subprocess
import paho.mqtt.client as mqtt # Import the MQTT library

MQTT_CLIENT_ID = "front_door_ringer"
MQTT_TOPIC = [("event/doorbell", 1), ("connection/ping", 1)]
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 120
MQTT_USER = ""
MQTT_PASS = ""
SOUNDS_FOLDER = "/home/pi/DoorBell/sounds/"

class DoorBell_Ringer:
    def __init__(self):
        """ Initialise member variables """
        self.playing = []  # List of dings and dongs
        self.limit_number = 4
        self.selected_ding = "ding.wav"
        self.selected_dong = "dong.wav"
        self.killed = False

        # MQTT Initialisation
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=False)
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe

        self.client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        self.client.loop_start() # Start the MQTT client

    def Ding(self):
        """ Play Ding Sound """
        self.processPlaying(self.playing, self.limit_number)
        filename = SOUNDS_FOLDER + self.selected_ding
        if self.selected_ding != "" and os.path.isfile(filename):
            self.playing.append(
                subprocess.Popen(["/usr/bin/aplay", '-q', filename])
            )

    def Dong(self):
        """ Play Dong Sound """
        self.processPlaying(self.playing, self.limit_number)
        filename = SOUNDS_FOLDER + self.selected_dong
        if self.selected_dong != "" and os.path.isfile(filename):
            self.playing.append(
                subprocess.Popen(["/usr/bin/aplay", '-q', filename])
            )

    def processPlaying(self, playing, limit_number):
        """ Remove finished sound processes and
            limit sound processes to a set number """
        count = len(playing)
        if (count >= limit_number):
            # Remove the first few until process count is low enough
            for n in range(0, (count-limit_number)):
                item = playing[0]
                if item.poll() is None:
                    item.terminate()  # Wasnt finished, make it finished
                playing.pop(0)  # remove first item from list

    def on_connect(self, mqttc, obj, flags, rc):
        print("Connected, rc: "+str(rc))
        self.client.subscribe(MQTT_TOPIC)

    def on_message(self, mqttc, obj, message):
        """ Message received. Do something  """
        print(message.topic+" "+str(message.qos)+" "+str(message.payload))
        topic = str(message.topic)
        message = str(message.payload.decode("utf-8"))
        if topic == MQTT_TOPIC[0][0]:
            if message == "DING":
                # Thin out audio playing list
                ringer.Ding()
                print("Ding")
            if message == "DONG":
                # Thin out audio playing list
                ringer.Dong()
                print("Dong")
        if topic == MQTT_TOPIC[1][0]:
            if message == "PING":
                print("MQTT Ping request")
                self.client.publish("connection/reply", MQTT_CLIENT_ID)

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def run(self):
        while True:
            time.sleep(1)

# Global variable to contain a single instance of the above class
#ringer = DoorBell_Ringer()


#def messageFunction (client, userdata, message):
#    """ static function to process any new messages """
#    global ringer
#    topic = str(message.topic)
#    message = str(message.payload.decode("utf-8"))
#    # print(topic + message)
#    if topic == TOPIC[0][0]:
#        if message == "DING":
#            # Thin out audio playing list
#            ringer.Ding()
#            print("Ding")
#        if message == "DONG":
#            # Thin out audio playing list
#            ringer.Dong()
#            print("Dong")


#def on_connect(client, userdata, flags, rc):
#    print("Connected with result code %s" % rc)
#    client.subscribe(TOPIC)


""" Main program loop """
#client = mqtt.Client(client_id=CLIENT_ID, clean_session=False) # Create a MQTT client object
#client.username_pw_set(MQTT_USER, MQTT_PASS)

# Set the on connect and on message callback functions
#client.on_connect = on_connect
#client.on_message = messageFunction

#client.connect(SERVER_IP, SERVER_PORT, KEEP_ALIVE)
#client.loop_start() # Start the MQTT client

#try:
#    while True:
#        time.sleep(1)
#except KeyboardInterrupt:
#    # Exit cleanly
#    pass
#finally:
#    client.loop_stop()



if __name__ == "__main__":
    ringer = DoorBell_Ringer()
    try:
        ringer.run()
    except:
        pass
    finally:
        ringer.client.loop_stop()
