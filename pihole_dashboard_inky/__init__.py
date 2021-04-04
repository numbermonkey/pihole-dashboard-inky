#!/usr/bin/env python3

# pihole-dashboard-inky
# Copyright (C) 2021  santoru
# modified for inky by numbermonkey
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import socket
from time import localtime, strftime
import urllib.request
import json
import os
import sys
import hashlib
import netifaces as ni
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

if os.geteuid() != 0:
    sys.exit("You need root permissions to access E-Ink display, try running with sudo!")

# STATIC VARIABLES
INTERFACE = "eth0"
PIHOLE_PORT = 80
OUTPUT_LINE1 = ""
OUTPUT_LINE2 = ""
OUTPUT_LINE3 = ""
OUTPUT_LINE4 = ""
OUTPUT_LINE5 = ""
FILENAME = "/tmp/.pihole-dashboard-inky-output"
hostname = socket.gethostname()
font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')
font_name = os.path.join(font_dir, "font.ttf")
font16 = ImageFont.truetype(font_name, 16)
font12 = ImageFont.truetype(font_name, 12)
PHadminURL = "http://127.0.0.1:{}/admin/api.php".format(PIHOLE_PORT)


# INKY SETUP
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

#def draw_dashboard(out_string=None):
def draw_dashboard(out_string1=None, out_string2=None, out_string3=None, out_string4=None, out_string5=None):
# Get Time
	t = strftime("%H:%M:%S", localtime())
	time_string = "T: {}".format(t)
# Get Version
	cmd = "/usr/local/bin/pihole -v"
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split('\n')
	version = output[0].split("(")[0].strip()
	
	img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
	draw = ImageDraw.Draw(img)

	draw.rectangle([(0, 87), (212, 104)], fill=1)
	if out_string1 is not None:
		fontS = font12
		fontL = font16
		drop = 1
		draw.text((1,drop),out_string1, inky_display.RED, fontS)
		w, h = fontS.getsize(out_string1)
		drop = drop + h + 2
		draw.text((1,drop),out_string2, inky_display.RED, fontS)
		w, h = fontS.getsize(out_string2)
		drop = drop + h + 2
		draw.text((1,drop),out_string3, inky_display.RED, fontS)
		w, h = fontS.getsize(out_string3)
		drop = drop + h + 2
		draw.text((1,drop),out_string4, inky_display.RED, fontS)
		w, h = fontS.getsize(out_string4)
		drop = drop + h + 2
		draw.text((1,drop),out_string5, inky_display.RED, fontS)
	draw.text((5,88), version, font=font12, fill=0)
	draw.text((150,88), time_string, font=font12, fill=0)
	inky_display.set_image(img)
	inky_display.show()


def update():


# Get Temp
	cmd = "/opt/vc/bin/vcgencmd"
	cmdopt = "measure_temp"
	process = subprocess.Popen([cmd, cmdopt], stdout=subprocess.PIPE)
	tempC = process.stdout.read()
# Get Load
#	cmd = "/usr/bin/uptime"
#	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
#	output = process.stdout.read().decode().split('\n')
#	version = output[0].split("(")[0].strip()
# Get Pihole Status
	cmd = "/usr/local/bin/pihole status"
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	PHstatus = process.stdout.read().decode().split('\n')
# Get Pihole Stats
	PHstats = json.load(urllib.request.urlopen(PHadminURL))
	unique_clients = PHstats['unique_clients']
	ads_blocked_today = PHstats['ads_blocked_today']

	try:
		ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
	except KeyError:
		ip_str = "[×] Can't connect to eth0"
		ip = ""

	if "192.168" in ip:
		ip_str = "[✓] IP of {}: {}".format(hostname, ip)

#CANT GET SINGLE STRING HASH FILE WORKING
#	OUTPUT_STRING = ip_str + "/n" + output[0].strip().replace('✗', '×') + "/n" + output[6].strip().replace('✗', '×')
#	OUTPUT_STRING = OUTPUT_STRING + "/n" + "[✓] There are {} clients connected".format(unique_clients)
#	OUTPUT_STRING = OUTPUT_STRING + "/n" + "[✓] Blocked {} ads".format(ads_blocked_today)
#	OUTPUT_LINE1 = ip_str
	OUTPUT_LINE1 = tempC
	OUTPUT_LINE2 = PHstatus[0].strip().replace('✗', '×')
	OUTPUT_LINE3 = PHstatus[6].strip().replace('✗', '×')
	OUTPUT_LINE4 = "[✓] There are {} clients connected".format(unique_clients)
	OUTPUT_LINE5 = "[✓] Blocked {} objects".format(ads_blocked_today)
#	hash_string = hashlib.sha1(OUTPUT_STRING.encode('utf-8')).hexdigest()
#	try:
#		hash_file = open(FILENAME, "r+")

#	except FileNotFoundError:
#		os.mknod(FILENAME)
#		hash_file = open(FILENAME, "r+")

#	file_string = hash_file.read()
#	if file_string != hash_string:
#		hash_file.seek(0)
#		hash_file.truncate()
#		hash_file.write(hash_string)
# DIFFERENT ATTEMPT
#	draw_dashboard(OUTPUT_STRING)
	draw_dashboard(OUTPUT_LINE1, OUTPUT_LINE2, OUTPUT_LINE3, OUTPUT_LINE4, OUTPUT_LINE5)
