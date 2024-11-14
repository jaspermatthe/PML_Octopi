# PML_Pi
The following equipment is used for this setup:
- [Raspberry Pi Model 4B](https://www.amazon.com/Raspberry-Model-2019-Quad-Bluetooth/dp/B07TC2BK1X/ref=sr_1_1?crid=3DQOZFPCZQPKF&dib=eyJ2IjoiMSJ9.4wZGiZcG7IfVeIs8ylcbrzsNv6dicwLzRFdua87NS7JXmE8c7PlGpbGZEDTRqd8Voac3t1ZJGzDtko-pnzA8PZ5wHFaROyMA1gE1jU6_JAL24_IywgU8h57N1WLhgk-J6s9VSZlK5PPvLGtH32XJbb2r3Wu9VJGEhBEOUlpF7WpXss7mHKSqWkMgOr4dBOtArKsnOS178Wvqsklfzbxu-4PTVNRZAyHsK3PNQuyNG2RympMsEtam5Tcw4BvaeyhCOvDWfcm2z1L75ZcndM-Fl81vvmFLXpzVGFNUh0XvdZ8.4miz5Xpm0GtiC9LKQfAtmroaWU5mpzwjLSDi32yb1yk&dib_tag=se&keywords=Raspberry%2BPi%2B4%2B4gb&qid=1727386287&s=electronics&sprefix=raspberry%2Bpi%2B4%2B4g%2Celectronics%2C163&sr=1-1&th=1)
- [Official RPi power supply](https://www.amazon.com/Raspberry-Pi-USB-C-Power-Supply/dp/B07W8XHMJZ/ref=sr_1_3?crid=3DGPIZXQJPVPL&dib=eyJ2IjoiMSJ9.9lnXH5NRICo8PtrSZbtmE2ZFvwxEXiQs00bphhBXuWpsPhiX6jUd-PFcZjfENHQLkcWmvowGg8iwLuvb4D7FrBgsUx5Eagrz5O9YTziSW6Xa-m2uFnepFWuv4Cjx1IO6UitPCYNzZ5_frWOFQtwNNl0ZjUNXLixAF4WXtnjf5Lr78T8tW4htDXoyB2mknEyI-l3oU7I5tYi5Z8XyWtE6dzVYnmPB5F3ZwGH8vu0tKBZukmfJz5v5M9qjmkGcAViUVmdo3t16S9-gaNIv5BmTSy_8m9lDzeGTLFvyGRuhaR0.KtSBuMeLsXI3Whsgkb-Kh0X64_gWBqUjm5HPoGtvf2g&dib_tag=se&keywords=raspberry+pi+4+power+supply&qid=1727385091&s=electronics&sprefix=raspberry+pi+4+power%2Celectronics%2C149&sr=1-3)
- Original Prusa i3 MK3
- [Logitech C270](https://www.amazon.com/Logitech-Desktop-Widescreen-Calling-Recording/dp/B004FHO5Y6?th=1)
- Desktop monitor
- HDMI to mini-HDMI cable
- [USB A to B Cable](https://www.amazon.com/UGREEN-Printer-Scanner-Brother-Lexmark/dp/B00P0FO1P0/ref=sr_1_1_sspa?crid=1SA95GARV7YOZ&dib=eyJ2IjoiMSJ9.EaNOJ0-g5Ugaua6ta-KqPtireURDs2HzGwAQdeG2LUlyfKOw1Si4xoF5FdOEEPZ6L03rsZI55LNUZvrnYaN67ciSnn9GuSxlfwiIJ1yRmdpZ2at22THNbbSj9tyOzjbi6HVTms-IaD5_I6oz6CRHU3rwY6rVEQH630F3Cd8KMPXO6zmlQ7CB6EFU3jX1hwtyLRFDRv5diqt5bnXDwk81pNzhKGINqvrZ0byn_UnCLd9nom1A71OieOJGbieh9NYFjBfi_1xljO4kgrnkQFF03o6_xOr6hy6Nd9nIQ0i8Zs8.RyViy8DvWEAggwNyQFUfKtrGpMD4I1zrBvqvZX-3pU0&dib_tag=se&keywords=USB%2BA%2Bto%2BB%2BCable&qid=1727385964&refinements=p_36%3A-900&rnid=386442011&s=electronics&sprefix=usb%2Ba%2Bto%2Bb%2Bcable%2Braspberry%2Celectronics%2C113&sr=1-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1)

This documentation is divided into two sections:
1. Raspberry Pi Octoprint Setup and Connection to Printer;
2. Octoprint Plugin Development

## 1. Raspberry Pi Octoprint server Setup
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

#### (Alternatively) you can SSH into the RPi to control it
1. Open a terminal on your computer
2. Enter:
    - ssh raspberry@YOUR_RPIs_IPADDRESS
    - the password

#### Test webcam and connection to printer.
1. Connect the printer to the RPi via the USB A to B cable.
2. Connect the webcam to the RPi via the camera's USB cable.
3. Restart the Octoprint server
## 2. Octoprint Plugin Development



