# Clean Dashboard for Pi-Hole CHANGED TO INKY
Minimal and clean dashboard to visualize some stats of Pi-Hole with an E-Ink display attached to your Raspberry Pi.

This is very useful if you keep a Pi Zero with Pi-Hole connected to your router and you want a clean dashboard to monitor its status.
<p align="center">
    <a href="https://pypi.org/project/pihole-dashboard/"><img alt="PyPI" src="https://img.shields.io/pypi/v/pihole-dashboard"></a>
    <a href="#"><img alt="Updated" src="https://img.shields.io/github/last-commit/santoru/pihole-dashboard?label=updated"></a>
    <a href="https://pi-hole.net/"><img alt="Powered-By" src="https://img.shields.io/badge/Powered--By-Pi--Hole-FF0000?logo=pi-hole"></a>
    <br/>
    <img src="/img/raspberry.jpg" alt="Raspberry Pi Zero" />
</p>

## My Setup
- Raspberry Pi Zero v1.3 (You can also solder the headers by yourself)
- <a href="https://shop.pimoroni.com/products/inky-phat?variant=12549254217811">2.13 inch E-Ink display HAT for Raspberry Pi</a>
- <a href="https://pi-hole.net/">Pi-Hole</a> (I have v5.2.4 at the moment)

## Configuration
The tool should run out of the box with standard installation of Pi-Hole. If you have a different setup probably the scripts should be adapted too.
If your instance of Pi-Hole is running on a different port than 80, you should change it inside `pihole_dashboard/__init__.py`.

### UPDATE BELOW FOR INKY PHAT
### WaveShare e-Paper dependency
Making the E-Ink display work is not fully covered here, as it depends mostly on the display you use. As said before, I have the Inky Phat 2.13 inch E-Ink display, that has a nice Getting Started guide here: https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-inky-phat.

You can find there the list of required dependencies for Python and how to run and test the provided examples.
Just for reference, this is the list of dependencies that should be installed on a Raspberry Pi Zero to configure the display I have:
```
sudo apt-get install python3-pip python3-pil python3-numpy
sudo pip3 install RPi.GPIO
sudo pip3 install spidev 
```
#In order to use the 2.13 inch E-Ink display with Python, you also need to get and build their `waveshare-epd` library:
#```bash
#git clone https://github.com/waveshare/e-Paper.git
#cd e-Paper/RaspberryPi_JetsonNano/python/
#sudo python3 setup.py install
#```
#You can check if the display is working by running the test example:
#```bash
#cd e-Paper/RaspberryPi_JetsonNano/python/
#sudo python3 examples/epd_2in13_V2_test.py
#```
#Remember that you need **root** access to control the display, so be sure to run the python example as root. 

#The example will print several geometric objects on the screen if everything is working as expected, followed by a simple clock program that updates every second.
#If the example does not work, do not proceed further with the installation as this probably will not work either.

## Installation
The installation requires to have already a Raspberry with Pi-Hole installed and correctly running, if you have problem installing Pi-Hole <a href="https://github.com/pi-hole/pi-hole">check their README</a>.

### Dependencies
Ensure that you have already this `Pillow` dependency installed:
```bash
sudo apt install libopenjp2-7
```
### From PyPI
```bash
sudo pip3 install pihole-dashboard
```
# CHANGED ?
### From Source
```bash
git clone https://github.com/santoru/pihole-dashboard-inky
cd pihole-dashboard-inky
sudo pip3 install .
```
Once installed, reboot the Raspberry Pi. The dashboard should appear few minutes after the reboot.

# CHANGED ?
## Uninstall
You can remove the tool anytime by running
```bash
sudo pip uninstall pihole-dashboard-inky
```
You can also manually remove the cronjob by running
```bash
sudo rm /etc/cron.d/pihole-dashboard-inky-cron
```

## How it works
The tool will install a Cron Job on the Raspberry Pi that will check the status of Pi-Hole every minute. If there's an update to display, the screen will refresh and update its content.

## Troubleshooting
If the dashboard is not displaying, you can check if the script return an error by running
```bash
sudo pihole-dashboard-inky-draw
```
If everything is working as expected, nothing will be printed out.
If you still have errors, please open an issue.
