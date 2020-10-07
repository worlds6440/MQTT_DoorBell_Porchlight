import time
import threading
import RPi.GPIO as GPIO
# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt
import porchlight

MQTT_CLIENT_ID = "doorbell_button"
MQTT_SUB_TOPIC = [("connection/ping", 1)]
MQTT_PUB_TOPIC = [("event/doorbell", 1), ("event/doorbell_app", 1), ("connection/reply", 1)]
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 120
MQTT_USER = ""
MQTT_PASS = ""

class DoorBell_Button():
    def __init__(self, GPIO):
        """ Initialise memeber variables """
        self.pin_button = 23

        self.time_pressed_last = time.time()
        self.time_released_last = time.time()
        # time gap in seconds
        self.time_gap = 1.0
        # List of dings and dongs
        self.playing = []
        self.limit_number = 4
        # max time allowed for holding button
        self.time_held_limit = 1
        self.isPressed = False
        self.veto_release = False

        self.GPIO = GPIO

        # Setup GPIO using BCM numbering
        self.GPIO.setmode(self.GPIO.BCM)

        # Set GPIO pins appropriately
        self.GPIO.setup(
            self.pin_button,
            self.GPIO.IN,
            pull_up_down=self.GPIO.PUD_DOWN
        )
        self.GPIO.add_event_detect(
            self.pin_button,
            self.GPIO.BOTH,
            callback=self.button
        )

        self.killed = False
        self.client = mqtt.Client(MQTT_CLIENT_ID, clean_session=False)  # Create a MQTT client object
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe

        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)  # Connect to the test MQTT broker
        self.client.loop_start()

    def on_connect(self, mqttc, obj, flags, rc):
        print("Connected, rc: "+str(rc))
        self.client.subscribe(MQTT_SUB_TOPIC)

    def on_message(self, mqttc, obj, message):
        """ Message received. Do something  """
        print(message.topic+" "+str(message.qos)+" "+str(message.payload))
        topic = str(message.topic)
        message = str(message.payload.decode("utf-8"))
        if topic == MQTT_SUB_TOPIC[0][0]:
            if message == "PING":
                print("MQTT Ping request")
                self.client.publish(MQTT_PUB_TOPIC[2][0], MQTT_CLIENT_ID)

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def run(self):
        """ Starting method. Listen for doorbell button
        press and inform all MQTT clients listening. """
        while True:
            # Check exit flag on each loop
            if self.killed:
                return
            else:
                # Dont run at 100% wasting CPU
                time.sleep(1)

    def Ding(self):
        """ Button pressed """
        # Send DING to all sockets
        print("Ding Sending")
        self.client.publish(MQTT_PUB_TOPIC[0][0], "DING")
        self.client.publish(MQTT_PUB_TOPIC[1][0], "DOORBELL")  # Separate single event for mobile MQTT apps

    def Dong(self):
        """ Button released """
        # Send DING to all sockets
        self.client.publish(MQTT_PUB_TOPIC[0][0], "DONG")  # Turn the AC unit on

    def button(self, channel):
        """ Button has been either pressed or released
        Its a rising or falling edge, check pin value to see which """
        pin_value = self.GPIO.input(self.pin_button)
        if (pin_value):
            self.buttonPressed(channel)
        else:
            self.buttonReleased(channel)

    def buttonPressed(self, channel):
        """ Button pressed """
        time_now = time.time()
        time_diff = time_now - self.time_pressed_last
        if (time_diff >= self.time_gap):
            # Time since previous press is longer than min gap
            self.isPressed = True
            # self.AppendDateToFile()
            self.Ding()
            # Remember last successful button press
            self.time_pressed_last = time_now

    def buttonReleased(self, channel):
        """ Button released """
        time_now = time.time()
        time_diff = time_now - self.time_released_last
        if (
            time_diff >= self.time_gap and
            not self.veto_release and
            self.isPressed
        ):
            # Time since previous press is longer than min gap
            self.isPressed = False
            self.Dong()
            # Remember last successful button press
            self.time_released_last = time_now
        # Reset variable
        self.veto_release = False


if __name__=="__main__":
    doorbell = DoorBell_Button(GPIO)
    doorbell.run()
