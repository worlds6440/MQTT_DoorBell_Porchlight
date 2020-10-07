# MQTT DoorBell Porchlight
Raspberry Pi powered MQTT enabled Doorbell with internal wav playing ringer and optional networked remote ringers. Works with MQTT dashboard apps (tested on android) for further extensibility.  
  
Automatic timed WS2812 LED Porchlights that change mode into external christmas lights with the auto festive mode.  
  
This repo is mainly a remote backup for my code but please feel free to use. NOTE folder locations in code will differ dependant to your install location.  
  
To run, `sudo crontab -e` and add the following lines  
`0 * * * * sh /home/pi/DoorBell/NTPUpdate.sh`  
`@reboot /usr/bin/python3 /home/pi/DoorBell/doorbell_button.py &`  
`@reboot /usr/bin/python3 /home/pi/DoorBell/porchlight.py &`  
`@reboot /home/pi/DoorBell/doorbell.sh`
