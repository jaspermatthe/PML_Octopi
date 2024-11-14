# PML_Pi
The following equipment is used for this setup:
- Raspberry Pi Model 4B
- Official RPi power supply
- Original Prusa i3 MK3
- Logitech C270
- Desktop monitor
- HDMI to mini-HDMI cable

This documentation is divided into two sections:
1. Raspberry Pi Octoprint Setup and Connection to Printer;
2. Octoprint Plugin Development

## 1. Raspberry Pi Octoprint Setup and Connection to Printer
### Booting an Octoprint Image to the Raspberry Pi
1. (https://www.youtube.com/watch?v=0FWOMdLVRjg) Use the Raspberry Pi Imager to write the **"Octoprint (Stable) Release"** to an SD card. Use the following **"Advanced Settings"** before writing:
    - Enable “Set hostname: raspberrypi1PML.local”
    - Enable “SSH, use password authentication”
    - Username: raspberry
    - Password: pi
2. In (an unpowered) Pi, insert the SD card with the Octoprint Image written to it
3. Power the RPi using USB-c power supply
4. Do not touch/unplug/power-off the RPi; wait ~5-10 minutes for the RPi to do its thing.
5. Once 10 minutes have passed or the green LED on the RPi stops blinking, setup should be done. Proceed to next step.

### Assigning a static IP Address to the Pi
_Instructions in this subsection are only valid for use at the UW - Seattle._

Now that the RPi has read the Octoprint Image off the SD card, it will have also written its identifiers to the SD card. We want to read these to help the RPi connect to the internet automatically upon being powered-up.
#### Find the RPi's MAC Address
1. Remove the SD card from the RPi
2. Plug in the SD card into your computer
3. Open the "rootfs" drive. Open the "syslog" file located at var\log\syslog
4. Use CTRL-F to find “macaddr”, log the most recent one. For example: "D8:3A:DD:A0:DF:1A". This is a unique identifier assigned to the RPi - it is it's "name" seen by the wifi network.

#### Create a UW MPSK device login:
Follow these instructions to set up a username and password assigned to the MAC Address of the RPi you found above: 
https://itconnect.uw.edu/tools-services-support/networks-connectivity/uw-networks/campus-wi-fi/uw-mpsk/. Take note of the username and password for the next step.

#### Change wifi settings on the RPi
Instructions from: https://community.octoprint.org/t/wifi-setup-and-troubleshooting/184.
1. Read SD card on laptop
2. Open "boot" drive
3. Change the wifi details in “octopi-wpa-supplicant.txt” according to what you set up for UW MPSK:
    - SSID: UW MPSK
    - Password: XXXXXXX
    - Wireless LAN country: US
4. Eject the SD card properly
5. Re-plug the SD card into the Pi

#### Request static IP address for the RPi
Follow instructions here: https://itconnect.uw.edu/tools-services-support/networks-connectivity/uw-networks/campus-wi-fi/wifi-static/. Providing all the details of the RPi.

Once your request is completed by UW IT, your RPi should be able to connect automatically to the UW MPSK wifi network upon being plugged in.

#### Plug in the RPi and connect to the Octoprint server
Make sure the RPi has its SD card plugged in.

1. Plug in the RPi
2. Wait until green LED stops blinking
3. Navigate to Pi’s IP address in a browser as found above.
4. Login with the username and password you specified 
    - Username: raspberry
    - Pwd: pi

You should now be logged into the Octoprint server.

Setup as guided and then backup your settings for future use:
Octoprint Settings→Backup and Restore

## 2. Octoprint Plugin Development



