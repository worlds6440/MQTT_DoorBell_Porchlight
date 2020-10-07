#!/usr/bin/env python3
import time
import ledstrip
import threading
from pixelpi import Strip
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 120
MQTT_CLIENT_ID = "front_door_lights"
MQTT_TOPIC = "event/porchlight"
MQTT_USER = ""
MQTT_PASS = ""

class PorchLight():

    def __init__(self):
        # Constructor
        # Member Vars
        self.DEBUG = False
        # Time for LED to turn ON
        self.onHour = 16
        self.onMin = 00
        # Time for LED to turn OFF
        self.offHour = 00
        self.offMin = 00
        # Thread lock
        self.lock = threading.Lock()
        self.exit = False  # flag set when we want the process to exit
        self.brightness = 255  # 0 - 255
        # "WS2812", "SK6812", "SK6812W", "SK6812_RGBW", "SK6812_RBGW", "SK6812_GRBW", "SK6812_GBRW", "SK6812_BRGW", "SK6812_BGRW", "WS2811_RGB", "WS2811_RBG", "WS2811_GRB", "WS2811_GBR", "WS2811_BRG", "WS2811_BGR"
        self.strip1 = Strip(terminal=2, size=5, shape='straight', ledtype='WS2812', brightness=self.brightness)
        self.strip2 = Strip(terminal=3, size=20, shape='straight', ledtype='WS2812', brightness=self.brightness)
        self.strip3 = Strip(terminal=4, size=150, shape='straight', ledtype='WS2812', brightness=self.brightness)

        # Create empty LED strip array
        self.channel = []

        # Add Red Channel LED strip (5 leds shown above)
        led_strip_1 = ledstrip.LedStrip(self.strip1)
        self.channel.append(led_strip_1)
        # Second LED Strip
        led_strip_2 = ledstrip.LedStrip(self.strip2, allow_seasonal_display=True)
        self.channel.append(led_strip_2)
        # Third LED Strip
        led_strip_3 = ledstrip.LedStrip(self.strip3, allow_seasonal_display=True)
        #led_strip_3.led_mode = led_strip_3.led_mode_three_spots
        led_strip_3.led_mode = led_strip_3.led_mode_every_third
        self.channel.append(led_strip_3)

        # If set 1, lights will turn on
        # if set 0, lights will turn off
        # if set -1, lights will revert to auto
        self.manual_override = -1

        # MQTT Initialisation
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=False)
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe

        self.client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        self.client.loop_start() # Start the MQTT client

    def set_exit(self):
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            self.exit = True
            # Set all channel threads to exit too
            for item in self.channel:
                item.set_exit()
        finally:
            # Release the list of sockets
            self.lock.release()

    def is_exit(self):
        # Grab the lock to the list of sockets
        isexit = False
        self.lock.acquire()
        try:
            # Fill list with socket information
            isexit = self.exit
        finally:
            # Release the list of sockets
            self.lock.release()
        return isexit

    def get_led_colour(self, channel):
        return self.channel[channel].get_led_colour()

    def set_led_colour(self, channel, red, green, blue):
        self.channel[channel].set_led_colour(red, green, blue)

    def set_all_led_colour(self, red, green, blue):
            # Set all channel threads to RGB colour
            for item in self.channel:
                self.set_led_colour(
                    item.channel,
                    red,
                    green,
                    blue
                )

    def shouldBeOn(self, timeNow):
        """ Returns whether lights should be on or off  """
        if self.DEBUG:
            print("HH:MM", timeNow.tm_hour, ':', timeNow.tm_min, timeNow.tm_sec)

        if self.manual_override == 0:
            return False
        elif self.manual_override == 1:
            return True
        else:
            # Convert On/Off times to minutes of the day
            onTime = self.onHour*60 + self.onMin
            offTime = self.offHour*60 + self.offMin
            curTime = timeNow.tm_hour*60 + timeNow.tm_min

            between = False
            if onTime < offTime:
                # Looking for a time between on/off
                between = True
            elif onTime > offTime:
                # Looking for a time between off/on
                between = False
            else:
                # On and Off time are the same
                between = False

            # Test whether the time is between or outside of the allotted range
            shouldBeOn = False
            if between:
                if onTime <= curTime and curTime < offTime:
                    shouldBeOn = True
            else:
                if onTime <= curTime or curTime < offTime:
                    shouldBeOn = True

            return shouldBeOn

    def is_in_date_range(self, start_month, start_day, end_month, end_day):
        """ Test whether todays date is within the given date range """
        # Get current date
        date = time.localtime()

        # Is start month greater than end month
        straddling_year_end = False
        if start_month > end_month:
            straddling_year_end = True

        # Is todays date on correct side of the start date
        within_start = False
        if date.tm_mon >= start_month and date.tm_mday >= start_day:
            within_start = True

        # Is todays date on correct side of the start date
        within_end = False
        if date.tm_mon <= end_month and date.tm_mday <= end_day:
            within_end = True

        # Test whether we are within date range
        if (
            (straddling_year_end and within_start and within_end)
            or
            (not straddling_year_end and (within_start or within_end))
        ):
            return True
        else:
            return False

    def on_connect(self, mqttc, obj, flags, rc):
        print("Connected, rc: "+str(rc))
        self.client.subscribe(MQTT_TOPIC, qos=1)

    def on_message(self, mqttc, obj, message):
        print(message.topic+" "+str(message.qos)+" "+str(message.payload))
        topic = str(message.topic)
        message = str(message.payload.decode("utf-8"))
        # print(topic + message)
        if topic == MQTT_TOPIC:
            if message == "ON":
                # We want lights to turn on now
                self.manual_override = 1
            if message == "OFF":
                # We want lights to turn off now
                self.manual_override = 0
            if message == "AUTO":
                # We want lights to turn off now
                self.manual_override = -1
            if message == "PARTY":
                # Ensure lights are off to start
                for item in self.channel:
                    if item.allow_seasonal_display:
                        # Turn light OFF
                        item.switch_off()
                self.manual_override = 1
                for item in self.channel:
                    if item.allow_seasonal_display:
                        # Then turn on party mode
                        item.switch_on_party_mode()

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def run(self):
        while True:
            try:
                # Ensure lights are off to start
                for item in self.channel:
                    # Turn light OFF
                    item.switch_off()

                # Loop indefinitely
                prev_should_be_on = False
                while True:
                    # Check exit flag on each loop
                    if self.is_exit():
                        return

                    # Get the time now
                    timeNow = time.localtime()

                    # Find out if the LEDS should be on
                    shouldBeOn = self.shouldBeOn(timeNow)

                    # Is there a change in On/Off state
                    led_state_change = False
                    christmas_display = False
                    if prev_should_be_on != shouldBeOn:
                        led_state_change = True
                        # Christmas Display Period
                        if self.is_in_date_range(12, 18, 1, 5):
                            christmas_display = True

                    for item in self.channel:
                        # If light allows seasonal display, set its
                        #  mode here BEFORE we turn it on
                        if (
                            led_state_change
                            and item.allow_seasonal_display
                        ):
                            # Changeover
                            if christmas_display:
                                item.led_mode = item.led_mode_christmas
                            else:
                                if item.led_count() >= 50:
                                    #item.led_mode = item.led_mode_three_spots
                                    item.led_mode = item.led_mode_every_third
                                else:
                                    item.led_mode = item.led_mode_standard

                        if shouldBeOn:
                            # Turn light ON
                            item.switch_on()
                        else:
                            # Turn light OFF
                            item.switch_off()

                    # Sleep for a minute and test again.
                    # NOTE: will always normalise the tick to round minutes
                    #time.sleep(60 - timeNow.tm_sec)
                    time.sleep(1)  # Simply check on/off status once a second. Should be no extra load
                    # Finally, remember the "should be on" state
                    prev_should_be_on = shouldBeOn
            except (KeyboardInterrupt, SystemExit):
                # Users pressed Ctrl+C
                self.off()
                return


if __name__=="__main__":
    lights = PorchLight()
    try:
        rc = lights.run()
        print("rc: " + str(rc))

    except:
        # Quitting, ensure lights are off
        for item in lights.channel:
            # Turn light OFF
            item.switch_off()
        lights.set_exit()
        pass
