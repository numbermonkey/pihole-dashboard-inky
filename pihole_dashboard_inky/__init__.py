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
import urllib.request
import json
import os
import sys
import hashlib
import re
import netifaces as ni
import gpiozero as gz
from time import localtime, strftime
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

if os.geteuid() != 0:
    sys.exit("You need root permissions to access E-Ink display, try running with sudo!")

# STATIC VARIABLES
INTERFACE = "eth0"
PIHOLE_PORT = 80
PH2IP = "192.168.1.85"
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
str1clr = 2
# Parameters for conditional text
cpucooltemp = 40.0
cpuoktemp = 65.0
cpubadtemp = 80.0
loadhigh = 0.7
utilhigh = 90.0

# INKY SETUP
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

def draw_dashboard(out_string1=None, str1clr=1, out_string2=None, out_string3=None, out_string4=None, out_string5=None):
# Get Time
	t = strftime("%H:%M:%S", localtime())
	time_string = "T: {}".format(t)
# Get Version
	cmd = "/usr/local/bin/pihole -v"
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split('\n')
	version = output[0].split("(")[0].strip()
# Init screen	
	img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
	draw = ImageDraw.Draw(img)
# Black rectangle at bottom
	draw.rectangle([(0, 87), (212, 104)], fill=1)
# Draws the text lines 
	if out_string1 is not None:
# 2 font sizes		
		fontS = font12
		fontL = font16
# gap from top
		drop = 1
# writes the out_strings and allows 1 line between them. Uses height of font to determine gap		
		draw.text((1,drop),out_string1, str1clr, fontL)
		w, h = fontL.getsize(out_string1)
		drop = drop + h + 1
		draw.text((1,drop),out_string2, inky_display.RED, fontL)
		w, h = fontL.getsize(out_string2)
		drop = drop + h + 1
		draw.text((1,drop),out_string3, inky_display.RED, fontS)
		w, h = fontS.getsize(out_string3)
		drop = drop + h + 1
		draw.text((1,drop),out_string4, inky_display.RED, fontS)
		w, h = fontS.getsize(out_string4)
		drop = drop + h + 1
		draw.text((1,drop),out_string5, inky_display.RED, fontS)
# Adds version and time to bottom box. Note the white font.		
	draw.text((5,88), version, font=font12, fill=0)
	draw.text((150,88), time_string, font=font12, fill=0)
# Send to Inky
	inky_display.set_image(img)
	inky_display.show()


def update():

# This def updates the text lines

# Get Temp
	cpu_temp = gz.CPUTemperature().temperature
	cpu_temp = round(cpu_temp, 1)
	if cpu_temp <= cpucooltemp:
		cputempstr = "[✓] Cool {}C".format(cpu_temp)
		cputempstrclr = 1
	if cpu_temp > cpucooltemp <= cpuoktemp:
		cputempstr = "[✓] Warm {}".format(cpu_temp)
		cputempstrclr = 1
	if cpu_temp > cpuoktemp <= cpubadtemp:
		cputempstr = "[✗] WARNING {}".format(cpu_temp)
		cputempstrclr = 2		
	if cpu_temp > cpubadtemp:
		cputempstr = "[✗] DANGER {}".format(cpu_temp)
		cputempstrclr = 2
# Get Load
	cmd = "/usr/bin/uptime"
	process = subprocess.Popen(cmd.split(','), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split(",")
	load5min = float(output[-2])
	last_idle = last_total = 0
	with open('/proc/stat') as f:
		fields = [float(column) for column in f.readline().strip().split()[1:]]
		idle, total = fields[3], sum(fields)
	idle_delta, total_delta = idle - last_idle, total - last_total
	utilisation = 100.0 * (1.0 - idle_delta / total_delta)
	utilisation = round(utilisation, 1)
	last_idle, last_total = idle, total
	if load5min >= loadhigh and utilisation >= utilhigh:
		loadstr = "[✗] DANGER Load:{} CPU:{}%".format(load5min,utilisation)
	if load5min >= loadhigh and utilisation < utilhigh:
		loadstr = "[✗] WARNING Load:{} CPU:{}%".format(load5min,utilisation)
	if load5min < loadhigh:
		loadstr = "[✓] Load:{} at CPU:{}%".format(load5min,utilisation)
# Get Pihole Status
	cmd = "/usr/local/bin/pihole status"
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	PHstatus = process.stdout.read().decode().split('\n')
# Get Pihole Stats
	PHstats = json.load(urllib.request.urlopen(PHadminURL))
	unique_clients = PHstats['unique_clients']
	ads_blocked_today = PHstats['ads_blocked_today']
	blockp = round(PHstats['ads_percentage_today'],1)
	if blockp == 0.0:
		blockpstr = "[✗] DANGER Block %:{}".format(blockp)
	if blockp > 0.0:
		blockpstr = "[✓] Blocked {} objects = {}%".format(ads_blocked_today,blockp)
# Get Gravity Age
	GravDBDays = PHstats['gravity_last_updated']['relative']['days']
	GravDBHours = PHstats['gravity_last_updated']['relative']['hours']
	if GravDBDays > 7:
		GDBagestr = "[✗] WARNING GDB Age:{} days".format(GravDBDays)
	if GravDBDays <= 7:
		GDBagestr = "[✓] GDB Age:{}dys {}hrs".format(GravDBDays,GravDBHours)
# Get IP Address
	try:
		ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
	except KeyError:
		ip_str = "[×] Can't connect to eth0"
		ip = ""
	if "192.168" in ip:
		ip_str = "[✓] IP of {}: {}".format(hostname, ip)

# Creates the different output lines based on above
	OUTPUT_LINE1 = cputempstr
	LINE1CLR = cputempstrclr
	OUTPUT_LINE2 = loadstr
	OUTPUT_LINE3 = GDBagestr
	OUTPUT_LINE4 = blockpstr
	OUTPUT_LINE5 = PHstatus[6].strip().replace('✗', '×')
#	OUTPUT_EXAMPLE = ip_str
#	OUTPUT_EXAMPLE = PHstatus[6].strip().replace('✗', '×')
#	OUTPUT_EXAMPLE = "[✓] There are {} clients connected".format(unique_clients)
#	OUTPUT_EXAMPLE = "[✓] Blocked {} objects".format(ads_blocked_today)
	draw_dashboard(OUTPUT_LINE1, LINE1CLR, OUTPUT_LINE2, OUTPUT_LINE3, OUTPUT_LINE4, OUTPUT_LINE5)
