# PML_Pi
The following equipment is used for this setup:
- Raspberry Pi Model 4B
- Original Prusa i3 MK3
- Logitech C270

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
Now that the RPi has read the Octoprint Image off the SD card, it will have also written its identiers to the SD card. We want to read these to help the RPi connect to the internet automatically upon being powered-up.
1. Remove the SD card from the RPi
2. 
Assign a static IP address to the Pi
Find the MAC Address of the Raspberry Pi
Plug in the SD card into your computer
Open rootfs drive → var → log → syslog file
Control f to find the “macaddr”, making sure you log the most recent one
Currently: D8:3A:DD:A0:DF:1A
Create a UW MPSK device login:
https://itconnect.uw.edu/tools-services-support/networks-connectivity/uw-networks/campus-wi-fi/uw-mpsk/
Follow the instructions to set up a username and password assigned to the MAC Address of the Pi you found above.
Change wifi settings on the Pi:
https://community.octoprint.org/t/wifi-setup-and-troubleshooting/184
Read SD card on laptop
Open boot drive
Change the wifi details in “octopi-wpa-supplicant.txt” according to what you set up for UW MPSK:
SSID: UW MPSK
Password: ;g-t5:acnM
Wireless LAN country: US
Eject properly
Request a static IP address for the Pi: https://itconnect.uw.edu/tools-services-support/networks-connectivity/uw-networks/campus-wi-fi/wifi-static/: 
IP Address of As of Oct 8, 2024: 10.18.2.98
Re-plug the SD card into the Pi
Go to Pi’s IP address in a browser as found above. 
Current login details:
Username: raspberry
Pwd: pi
You should now be logged into the Octoprint server.
Setup as guided and then backup your settings for future use:
Octoprint Settings→Backup and Restore


## 2. Octoprint Plugin Development



