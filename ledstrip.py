#!/usr/bin/env python
import math
import time
import threading
from random import randint


class LedStrip():

    def __init__(self, pixelpi_strip, allow_seasonal_display=None, led_mode=1):
        # Constructor
        self.pixelpi_strip = pixelpi_strip
        # LED On flag
        self.led_on = False
        # LED ON Colour
        self.led_red = 255
        self.led_green = 200
        self.led_blue = 100
        # Current LED Colour
        self.current_led_red = 0
        self.current_led_green = 0
        self.current_led_blue = 0
        # Thread lock
        self.lock = threading.Lock()
        self.exit = False  # flag set when we want the process to exit
        # Debug flag
        self.DEBUG = False
        # LED illumination mode enum values
        self.led_mode_standard = 1
        self.led_mode_christmas = 2
        self.led_mode_every_third = 3
        self.led_mode_three_spots = 4
        # LED illumination mode
        self.led_mode = led_mode
        self.allow_seasonal_display = False
        if allow_seasonal_display is not None:
            self.allow_seasonal_display = allow_seasonal_display
        # Thread pointer for christmas display (and any future mode)
        self.led_thread = None

    def set_exit(self):
        """ Tell this thread to stop """
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            self.exit = True
        finally:
            # Release the list of sockets
            self.lock.release()

    def is_exit(self):
        """ Has this thread been told to stop """
        return self.exit

    def get_led_colour(self):
        """ Get the LED RGB Values """
        red = self.led_red
        green = self.led_green
        blue = self.led_blue
        return red, green, blue

    def set_led_colour(self, red, green, blue):
        """ Set the LED RGB Values """
        self.lock.acquire()
        try:
            self.led_red = red
            self.led_green = green
            self.led_blue = blue
        finally:
            self.lock.release()
        # If LED already on, change colour immediately
        if self.is_on():
            self.set_all(red, green, blue)
        return

    def get_current_led_colour(self):
        """ Get the current working LED RGB Values """
        red = self.current_led_red
        green = self.current_led_green
        blue = self.current_led_blue
        return red, green, blue

    def set_current_led_colour(self, red, green, blue):
        """ Set the current working LED RGB Values """
        self.lock.acquire()
        try:
            self.current_led_red = red
            self.current_led_green = green
            self.current_led_blue = blue
        finally:
            self.lock.release()
        return

    def is_on(self):
        """ Are the LEDs on """
        return self.led_on

    def set_on(self, led_on):
        """ Set the LEDs on flag """
        self.lock.acquire()
        try:
            self.led_on = led_on
        finally:
            self.lock.release()
        return

    def led_count(self):
        # Get appropriate LED count for current channel
        led_count = len(self.pixelpi_strip.getLEDs())
        return led_count

    def set_all(self, red, green, blue):
        """ Set all leds to a specific colour """
        if self.DEBUG:
            print("Colour ", str(red), str(green), str(blue))

        # Get appropriate LED count for current channel

        self.lock.acquire()
        try:
            led_count = self.led_count()
            # Loop leds and set RGB values
            for pixel in range(led_count):
                self.pixelpi_strip.setLEDs(rgb=(red, green, blue), led=pixel)
            # Single call to send RGB values
            self.pixelpi_strip.showLEDs()
        finally:
            self.lock.release()
        # Update what colour this class thinks its set too.
        self.set_current_led_colour(red, green, blue)
        return

    def phase_lights(self, fromR, fromG, fromB, toR, toG, toB):
        """ Gently change leds from a set color to another colour """
        timeSpan = 1.0  # seconds
        steps = 50  # static number of steps
        interval = timeSpan / steps

        # print("Int: {}, from {} {} {} to {} {} {}\n".format(interval, fromR, fromG, fromB, toR, toG, toB))

        # Calculate difference for each colour band
        red_diff = toR-fromR
        green_diff = toG-fromG
        blue_diff = toB-fromB

        # Using band difference, calculate
        # interval per colour band for each step
        red_int = (float(red_diff) / steps)
        green_int = (float(green_diff) / steps)
        blue_int = (float(blue_diff) / steps)

        if self.DEBUG:
            print("Interval ", str(red_int), str(green_int), str(blue_int))

        # Set the leds colour for each step
        red = float(fromR)
        green = float(fromG)
        blue = float(fromB)
        for i in range(0, steps):
            # print("{} {} {}\n".format( int(red), int(green), int(blue)))

            self.set_all(int(red), int(green), int(blue))
            red += red_int
            green += green_int
            blue += blue_int
            time.sleep(interval)

        # Finally, ensure we reach the final colour
        self.set_all(toR, toG, toB)

    def switch_on(self, force=False):
        """ Switch the lights on (if not already on) """
        if not self.is_on() or force:
            if self.led_mode == self.led_mode_standard:
                # Get current LED colour and colour it should be
                r, g, b = self.get_led_colour()
                current_r, current_g, current_b = self.get_current_led_colour()
                # Phase the lights from current to new values
                self.phase_lights(current_r, current_g, current_b, r, g, b)

            if self.led_mode == self.led_mode_every_third:
                # Turn every other (or multiple of) on
                r, g, b = self.get_led_colour()
                self.effect_every_other(4, r, g, b)

            if self.led_mode == self.led_mode_three_spots:
                # Set 3 spot lights at equal spacing
                r, g, b = self.get_led_colour()
                self.effect_three_spots(r, g, b)

            if self.led_mode == self.led_mode_christmas:
                # Kick off internal thread to constantly change lights
                if self.led_thread is None:
                    # Ensure thread killing flag is cleared
                    self.exit = False
                    # Kick off new thread listening for doorbell events
                    self.led_thread = threading.Thread(
                        target=self.christmas_display_1
                        #target=self.christmas_display_2
                    )
                    self.led_thread.start()
            # Set flag
            self.set_on(True)

    def switch_off(self, force=False):
        """ Switch the lights off (if not already off) """
        if self.is_on() or force:
            if self.led_thread is None:
                # Get current LED colour and colour it should be
                current_r, current_g, current_b = self.get_current_led_colour()
                # Phase the lights from current to new values
                self.phase_lights(current_r, current_g, current_b, 0, 0, 0)
            else:
                # ensure thread is killed
                self.set_exit()
                # Wipe thread pointer
                self.led_thread = None
            # Set flag
            self.set_on(False)

    def switch_on_party_mode(self):
        self.switch_off(True)
        # Ensure thread killing flag is cleared
        self.exit = False
        # Kick off new thread listening for doorbell events
        self.led_thread = threading.Thread(
            target=self.party_mode
        )
        self.led_thread.start()

    def spot(self, start_index, spot_size, r, g, b):
        """ Create a spotlight starting at an index """
        half_size = int(spot_size / 2)
        low_percent = 0.1
        high_percent = 1.0
        percent_diff = high_percent - low_percent
        percent_increment = percent_diff / half_size

        self.lock.acquire()
        try:

            # Increasing Brightness
            percent = low_percent
            for i in range(0, half_size-1):
                self.pixelpi_strip.setLEDs(rgb=(int(float(r)*percent), int(float(g)*percent), int(float(b)*percent)), led=start_index + i)
                percent = percent + percent_increment

            middle_pixel = spot_size - (half_size * 2)
            if middle_pixel == 1:
                self.pixelpi_strip.setLEDs(rgb=(r, g, b), led=(start_index + half_size))

            # Decreasing Brightness
            for i in range(0, half_size-1):
                self.pixelpi_strip.setLEDs(rgb=(int(float(r)*percent), int(float(g)*percent), int(float(b)*percent)), led=start_index + i)
                percent = percent - percent_increment

            # Single call to send RGB values
            self.pixelpi_strip.showLEDs()
        finally:
            self.lock.release()

    def effect_three_spots(self, r, g, b):
        """ Create 3 evenly spaced light clusters  """
        spot_size = 10
        led_count = self.led_count()
        gap = int(led_count - (3 * spot_size)) / 2

        self.spot(0, spot_size, r, g, b)
        self.spot(int(spot_size + gap), spot_size, r, g, b)
        self.spot(int((led_count - 1) - spot_size), spot_size, r, g, b)

    def effect_every_other(self, every, r, g, b):
        """ Set every third led to the colour specified """
        led_count = self.led_count()
        self.lock.acquire()
        try:
            from_index = 0
            # Set every other LED to the required colour
            for i in range(from_index, (led_count-1), every):
                self.pixelpi_strip.setLEDs(rgb=(r, g, b), led=i)
            # Single call to send RGB values
            self.pixelpi_strip.showLEDs()
        finally:
            self.lock.release()

    def effect_set_even_odd(self, red=None, green=None, blue=None, even=True):
        """ Set all even indexed LEDs a certain colour """
        # Maximum R G or B value
        max_value = 255

        r = 0
        g = 0
        b = 0

        # Choose a random colour limited to between 0 and 255
        if red is None:
            r = randint(0, max_value)
        else:
            r = red
        if green is None:
            g = randint(0, max_value)
        else:
            g = green
        if blue is None:
            b = randint(0, max_value)
        else:
            b = blue

        led_count = self.led_count()

        # Send to LEDs
        self.lock.acquire()
        try:
            # Calculate start index depending on whether
            # working with even or odd numbers
            from_index = 0
            if not even:
                from_index = 1
            # Set every other LED to the required colour
            for i in range(from_index, (led_count-1), 2):
                self.pixelpi_strip.setLEDs(rgb=(r, g, b), led=i)
            # Single call to send RGB values
            self.pixelpi_strip.showLEDs()
        finally:
            self.lock.release()

    def effect_swipe(self, red=None, green=None, blue=None, forwards=True):
        """ Turn all LEDs on in a swiping motion """
        # Maximum R G or B value
        max_value = 255

        r = 0
        g = 0
        b = 0

        # Choose a random colour limited to between 0 and 255
        if red is None:
            r = randint(0, max_value)
        else:
            r = red
        if green is None:
            g = randint(0, max_value)
        else:
            g = green
        if blue is None:
            b = randint(0, max_value)
        else:
            b = blue

        # calculate loop range for forwards or backwards
        led_count = self.led_count()
        from_index = 0
        to_index = led_count
        if not forwards:
            from_index = led_count-1
            to_index = -1

        # Loop LED indices
        x = from_index
        while x != to_index:
            self.lock.acquire()
            try:
                # Set LEDs colour
                self.pixelpi_strip.setLEDs(rgb=(r, g, b), led=x)
                self.pixelpi_strip.showLEDs()
            finally:
                self.lock.release()
            # Sleep a small while between each LED setting
            time.sleep(0.05)
            # Increment loop index
            if forwards:
                x = x+1
            else:
                x = x-1

    def millis(self):
        """ Return the current time in milliseconds  """
        return int(round(time.time() * 1000))

    def party_mode(self):
        """ Bouncing Balls """
        BallCount = 3
        red = 0
        green = 0
        blue = 255
        NUM_LEDS = self.led_count()
        Gravity = -9.81
        StartHeight = 1

        Height = [float] * BallCount
        ImpactVelocityStart = math.sqrt( -2 * Gravity * StartHeight )
        ImpactVelocity = [float] * BallCount
        TimeSinceLastBounce = [float] * BallCount
        Position = [int] * BallCount
        ClockTimeSinceLastBounce = [int] * BallCount
        Dampening = [float] * BallCount

        for i in range(0, BallCount-1):
            ClockTimeSinceLastBounce[i] = self.millis()
            Height[i] = StartHeight
            Position[i] = 0
            ImpactVelocity[i] = ImpactVelocityStart
            TimeSinceLastBounce[i] = 0
            Dampening[i] = 0.90 - float(i)/(BallCount**2)


        while True:
            # Check exit flag on each loop
            if self.is_exit():
                # Turn LEDs off if display exited
                self.set_all(0, 0, 0)
                return

            for i in range(0, BallCount-1):
                TimeSinceLastBounce[i] =  self.millis() - ClockTimeSinceLastBounce[i]
                Height[i] = 0.5 * Gravity * ( (TimeSinceLastBounce[i]/1000)**2.0 ) + ImpactVelocity[i] * TimeSinceLastBounce[i]/1000
                if Height[i] < 0:
                    Height[i] = 0
                    ImpactVelocity[i] = Dampening[i] * ImpactVelocity[i]
                    ClockTimeSinceLastBounce[i] = self.millis()

                    if ImpactVelocity[i] < 0.01:
                        ImpactVelocity[i] = ImpactVelocityStart
                Position[i] = round( Height[i] * (NUM_LEDS - 1) / StartHeight)

            self.lock.acquire()
            try:
                for i in range(0, BallCount-1):
                    self.pixelpi_strip.setLEDs(rgb=(red, green, blue), led=Position[i])

                self.pixelpi_strip.showLEDs()
            finally:
                self.lock.release()
            self.set_all(0, 0, 0)

    def christmas_display_1(self):
        """ Loop indefinitely displaying
        christmassy themed lighting display """
        while True:
            # Check exit flag on each loop
            if self.is_exit():
                # Turn LEDs off if display exited
                self.set_all(0, 0, 0)
                return

            self.effect_set_even_odd(255, 0, 0, even=True)
            self.effect_set_even_odd(0, 255, 0, even=False)
            # Pause for a small time
            time.sleep(0.5)

            self.effect_set_even_odd(0, 255, 0, even=True)
            self.effect_set_even_odd(255, 0, 0, even=False)
            # Pause for a small time
            time.sleep(0.5)

    def christmas_display_2(self):
        try:
            forwards = True
            while True:
                # Check exit flag on each loop
                if self.is_exit():
                    # Turn LEDs off if display exited
                    self.set_all(0, 0, 0)
                    return

                # Swipe the LEDs on with random colours
                self.effect_swipe(
                    red=None,
                    green=None,
                    blue=None,
                    forwards=forwards
                )
                # Sleep a small while between each LED setting
                time.sleep(0.05)
                # Swipe the LEDs off
                self.effect_swipe(
                    red=0,
                    green=0,
                    blue=0,
                    forwards=forwards
                )
                # Invert forwards flag each time
                forwards = not forwards

        except KeyboardInterrupt:
            self.off()
            return
