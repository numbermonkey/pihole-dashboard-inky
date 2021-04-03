#!/usr/bin/env python3

# pihole-dashboard-inky
# Copyright (C) 2021  santoru
# modified for inky numbermonkey
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
# REPLACE WITH SOMETHING INKY 
# from waveshare_epd import epd2in13_V2
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

if os.geteuid() != 0:
    sys.exit("You need root permissions to access E-Ink display, try running with sudo!")

#CHANGED BELOW LINE FROM WLAN0 SINCE I AM WIRED :)
INTERFACE = "eth0"
PIHOLE_PORT = 80

#CHANGE DUE TO LACK OF MULTILINE
#OUTPUT_STRING = ""
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

# ADD INKY SETUP LINES
# epd = epd2in13_V2.EPD()
# epd.init(epd.FULL_UPDATE)
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

def draw_dashboard(out_string1=None, out_string2=None, out_string3=None, out_string4=None, out_string5=None):

# 	BELOW LINES BUT FOR INKY
#    image = Image.new("1", (epd.height, epd.width), 255)
#    draw = ImageDraw.Draw(image)
	img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
	draw = ImageDraw.Draw(img)

# Get Time
	t = strftime("%H:%M:%S", localtime())
	time_string = "T: {}".format(t)
# Get Version
	cmd = "/usr/local/bin/pihole -v"
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split('\n')
	version = output[0].split("(")[0].strip()

#INKY PHAT CORRECTED COORDS & COLOURS
#   draw.rectangle([(0, 105), (250, 122)], fill=0)
	draw.rectangle([(0, 87), (212, 104)], fill=1)
	if out_string1 is not None:
#  AH, I SEE. THAT HASHY THING CONVERTS THE OUTPUT STRING INTO A SINGLE LINE OF TEXT WITH UTF CRs. 
#  I DONT THINK I CAN BE THAT SOPHISTICATED
#  MULTI LINE IS NOT AVAILABLE AND I'LL TRY WITHOUT THE HASHY THING FIRST
#  BELOW IS ORIGINAL CODE LINE
#        draw.text((0, 0), out_string, font=font16, fill=0)
		font = font12
		drop = 1
		draw.text((1,drop),out_string1, inky_display.RED, font)
		w, h = font12.getsize(out_string1)
		drop = drop + h +2
		draw.text((1,drop),out_string2, inky_display.RED, font)
		w, h = font12.getsize(out_string2)
		drop = drop + h +2
		draw.text((1,drop),out_string3, inky_display.RED, font)
		w, h = font12.getsize(out_string3)
		drop = drop + h +2
		draw.text((1,drop),out_string4, inky_display.RED, font)
		w, h = font12.getsize(out_string4)
		drop = drop + h + 2
		draw.text((1,drop),out_string5, inky_display.RED, font)
#    draw.text((5, 106), version, font=font12, fill=1)
	draw.text((5,88), version, font=font12, fill=0)
#    draw.text((150, 106), time_string, font=font12, fill=1)
	draw.text((150,88), time_string, font=font12, fill=0)
#	BELOW LINE BUT FOR INKY
#    epd.display(epd.getbuffer(image))
	inky_display.set_image(img)
	inky_display.show()


def update():
	url = "http://127.0.0.1:{}/admin/api.php".format(PIHOLE_PORT)
	r = json.load(urllib.request.urlopen(url))

	try:
		ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
	except KeyError:
		ip_str = "[×] Can't connect to eth0"
		ip = ""

	unique_clients = r['unique_clients']
	ads_blocked_today = r['ads_blocked_today']

	if "192.168" in ip:
		ip_str = "[✓] IP of {}: {}".format(hostname, ip)

	cmd = "/usr/local/bin/pihole status"
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split('\n')
#CANT DO MULTILINE
#	OUTPUT_STRING = ip_str + "\n" + output[0].strip().replace('✗', '×') + "\n" + output[6].strip().replace('✗', '×')
#    OUTPUT_STRING = OUTPUT_STRING + "\n" + "[✓] There are {} clients connected".format(unique_clients)
#    OUTPUT_STRING = OUTPUT_STRING + "\n" + "[✓] Blocked {} ads".format(ads_blocked_today)
	OUTPUT_LINE1 = ip_str
	OUTPUT_LINE2 = output[0].strip().replace('✗', '×')
# STATIC FOR TESTING
# OUTPUT_LINE2 = "[✓] DNS service is listening"
	OUTPUT_LINE3 = output[6].strip().replace('✗', '×')
# STATIC FOR TESTING 
# OUTPUT_LINE3 = "[✓] Pi-hole blocking is enabled"
	OUTPUT_LINE4 = "[✓] There are {} clients connected".format(unique_clients)
	OUTPUT_LINE5 = "[✓] Blocked {} ads".format(ads_blocked_today)
#  I DONT KNOW WHAT THE FOLLOWING CODE DOES
#    hash_string = hashlib.sha1(OUTPUT_STRING.encode('utf-8')).hexdigest()
#    try:
#        hash_file = open(FILENAME, "r+")
#
#    except FileNotFoundError:
#        os.mknod(FILENAME)
#        hash_file = open(FILENAME, "r+")
#
#    file_string = hash_file.read()
#    if file_string != hash_string:
#        hash_file.seek(0)
#        hash_file.truncate()
#        hash_file.write(hash_string)
# NEEDS TO CHANGE CANT DO MULTILINE
#   draw_dashboard(OUTPUT_STRING)
	draw_dashboard(OUTPUT_LINE1, OUTPUT_LINE2, OUTPUT_LINE3, OUTPUT_LINE4, OUTPUT_LINE5)
