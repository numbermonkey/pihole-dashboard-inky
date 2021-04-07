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
hostname = socket.gethostname()
font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')
font_name = os.path.join(font_dir, "font.ttf")
fontL = ImageFont.truetype(font_name, 16)
fontS = ImageFont.truetype(font_name, 12)
PHapiURL = "http://127.0.0.1:{}/admin/api.php".format(PIHOLE_PORT)
PH2apiURL = "http://192.168.1.85:{}/admin/api.php".format(PIHOLE_PORT)

# Parameters for conditional text
cpucooltemp = 40.0
cpuoktemp = 65.0
cpubadtemp = 80.0
loadhigh = 0.7
utilhigh = 90.0
blockpbad = 0.0
GravDBDaysbad = 7
	
# INKY SETUP
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

# Def has 5 lines of text. Each needs 3 arguments: txt (content), clr (colour 0=White, 1=Black, 2=Red) ,fnt (font - defined in static section)
def draw_dashboard(str1txt=None, str1clr=1, str1fnt=None, str2txt=None, str2clr=1, str2fnt=None, str3txt=None, str3clr = 1, str3fnt=None, str4txt=None, str4clr = 1, str4fnt=None, str5txt=None, str5clr = 1, str5fnt=None):

# THIS DEF DRAWS THE FINAL SCREEN
# Get Time
	t = strftime("%H:%M:%S", localtime())
	timestrtxt = "@ {}".format(t)
# Get Version
	cmd = "/usr/local/bin/pihole"
#	cmd = "/usr/local/bin/pihole -v"
# dont like popen for this purpose
#	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
#	output = process.stdout.read().decode().split('\n')
#	version = output[0].split("(")[0].strip()
	cmd = "/usr/local/bin/pihole"
	process = subprocess.run([cmd, "-v"], capture_output=True)
	output = process.stdout.decode()
	char = output.index('v',11)
	lclver = output[char+1:char+6]
	process = subprocess.run(["git", "ls-remote", "--tags", "https://github.com/pi-hole/pi-hole"], capture_output=True)
	repover = process.stdout.decode()[-6:].rstrip()
	if lclver == repover:
			boxclr = 1
			verstrtxt = "Pi-hole version is v{}".format(lclver)
			verstrfnt = timestrfnt = fontS
			verstrclr = timestrclr = 0
			
	elif repover > lclver:
			boxclr = 2
			verstrtxt = "UPDATE AVAILABLE"
			verstrfnt = timestrfnt = fontL
			verstrclr = timestrclr = 1
			
	print(lclver,"  ",repover,"  ",timestrtxt)
#	** just trying something **
#	cmd = "sudo git ls-remote --tags https://github.com/pi-hole/pi-hole | tail -1|cut --delimiter='v' -f2"
#	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
#	repoVer = process.stdout.read()
#	process = subprocess.run(cmd, capture_output=True)
#	repoVer = subprocess.CompletedProcess.stdout
#	cmd = "/usr/local/bin/pihole -v | cut -c 23-27 | head -n 1"
#	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
#	localVer = process.stdout.read()	
#	process = subprocess.run(cmd, capture_output=True)
#	repoVer = subprocess.CompletedProcess.stdout
#	print("Repo ver:",repoVer," Local ver:",localVer)
# Init screen	
	img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
	draw = ImageDraw.Draw(img)
# Draws the text lines 
	if str1txt is not None:
# gap from top
		drop = 1
# draws the str txts and allows 1 line between them. Uses height of font to determine gap		
		draw.text((1,drop),str1txt, str1clr, str1fnt)
		w, h = str1fnt.getsize(str1txt)
		drop = drop + h + 1
		draw.text((1,drop),str2txt, str2clr, str2fnt)
		w, h = str2fnt.getsize(str2txt)
		drop = drop + h + 1
		draw.text((1,drop),str3txt, str3clr, str3fnt)
		w, h = str3fnt.getsize(str3txt)
		drop = drop + h + 1
		draw.text((1,drop),str4txt, str4clr, str4fnt)
		w, h = str4fnt.getsize(str4txt)
		drop = drop + h + 1
		draw.text((1,drop),str5txt, str5clr, str5fnt)
# Black rectangle at bottom
	draw.rectangle([(0, 87), (212, 104)], fill=boxclr)
# Adds version and time to bottom box. Note the white font.		
	draw.text((5,88), verstrtxt, verstrclr, verstrfnt)
	draw.text((150,88), timestrtxt, timestrclr, timestrfnt)
# Send to Inky
	inky_display.set_image(img)
	inky_display.show()

def update():

# THIS DEF UPDATES THE TEXT LINES
# Read the PH api values
	PHstats = json.load(urllib.request.urlopen(PHapiURL))
	PH2stats = json.load(urllib.request.urlopen(PH2apiURL))
# Get Temp
	# Query for the temperature
	cpu_temp = gz.CPUTemperature().temperature
	cpu_temp = round(cpu_temp, 1)
	# Conditions for text output
	if cpu_temp <= cpucooltemp:
		cputempstr = "[✓] Cool {}C".format(cpu_temp)
		cputempstrclr = 1
		cputempstrfnt = fontS
	elif cpu_temp > cpucooltemp <= cpuoktemp:
		cputempstr = "[✓] Warm {}".format(cpu_temp)
		cputempstrclr = 1
		cputempstrfnt = fontL
	elif cpu_temp > cpuoktemp <= cpubadtemp:
		cputempstr = "[✗] WARNING {}".format(cpu_temp)
		cputempstrclr = 2
		cputempstrfnt = fontL
	elif cpu_temp > cpubadtemp:
		cputempstr = "[✗] DANGER {}".format(cpu_temp)
		cputempstrclr = 2
		cputempstrfnt = fontL
	print(cputempstr)
# Get Load
	# Get Load 5 min from uptime
	cmd = "/usr/bin/uptime"
	process = subprocess.Popen(cmd.split(','), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split(",")
	load5min = float(output[-2])
	# Get CPU %age from stat
	last_idle = last_total = 0
	with open('/proc/stat') as f:
		fields = [float(column) for column in f.readline().strip().split()[1:]]
		idle, total = fields[3], sum(fields)
	idle_delta, total_delta = idle - last_idle, total - last_total
	utilisation = 100.0 * (1.0 - idle_delta / total_delta)
	utilisation = round(utilisation, 1)
	last_idle, last_total = idle, total
	# Conditions for text output
	if load5min < loadhigh:
		loadstr = "[✓] Load: {} at CPU: {}%".format(load5min,utilisation)
		loadstrclr = 1
		loadstrfnt = fontS
	elif load5min >= loadhigh and utilisation < utilhigh:
		loadstr = "[✗] Load:{} CPU:{}%".format(load5min,utilisation)
		loadstrclr = 2
		loadstrfnt = fontL
	elif load5min >= loadhigh and utilisation >= utilhigh:
		loadstr = "[✗] DANGER Load:{} CPU:{}%".format(load5min,utilisation)
		loadstrclr = 2
		loadstrfnt = fontL
	print(loadstr)
# Get Pihole Status
	# Use api JSON
	PHstatus = PHstats['status']
	PH2status = PH2stats['status']
	# Conditions for text output
	if PHstatus == PH2status == "enabled":
		PHstatusstr = "[✓] Status PH1:[✓] PH2:[✓]"
		PHstatusstrclr = 1
		PHstatusstrfnt = fontS
	elif PHstatus != "enabled" and PH2status == "enabled":
		PHstatusstr = "[✗] Status PH1:[✗] PH2:[✓]"
		PHstatusstrclr = 2
		PHstatusstrfnt = fontL
	elif PHstatus == "enabled" and PH2status != "enabled":
		PHstatusstr = "[✗] Status PH1:[✓] PH2:[✗]"
		PHstatusstrclr = 2
		PHstatusstrfnt = fontL
	else:
		PHstatusstr = "[✗][✗] PH1:[✗] PH2:[✗]"
		PHstatusstrclr = 2
		PHstatusstrfnt = fontL
		
# Moved print(PHstatusstr) down to better emulate display
# GET PIHOLE STATS
	# First for local PH. Uses api JSON
	unique_clients = PHstats['unique_clients']
	ads_blocked_today = PHstats['ads_blocked_today']
	blockp = round(PHstats['ads_percentage_today'],1)
	# Then for 2nd PH. Uses api JSON
	unique_clients2 = PH2stats['unique_clients']
	ads_blocked_todayPH2 = PH2stats['ads_blocked_today']
	blockpPH2 = round(PH2stats['ads_percentage_today'],1)
	# Conditions for text output
	if blockp > blockpbad and blockpPH2 > blockpbad:
		blockpstr = "[✓] PH1: {}%  PH2: {}%".format(blockpPH2,blockp)
		blockpstrclr = 1
		blockpstrfnt = fontS
	elif blockp <= blockpbad:
		blockpstr = "[✗] DANGER Block % PH2:{}".format(blockp)
		blockpstrclr = 2
		blockpstrfnt = fontL
	elif blockpPH2 <= blockpbad:
		blockpstr = "[✗] DANGER Block % PH1:{}".format(blockpPH2)
		blockpstrclr = 2
		blockpstrfnt = fontL
	print(blockpstr)
	print(PHstatusstr)
# GET GRAVITY AGE
	# First for local PH. Uses api JSON
	GravDBDays = PHstats['gravity_last_updated']['relative']['days']
	GravDBHours = PHstats['gravity_last_updated']['relative']['hours']
	# Then for 2nd PH. Uses api JSON
	GravDBPH2Days = PH2stats['gravity_last_updated']['relative']['days']
	GravDBPH2Hours = PH2stats['gravity_last_updated']['relative']['hours']
	# Conditions for text output
#	if GravDBDays == GravDBPH2Days == 0:
#		GDBagestr = "[✓] GDB Recent"
#		GDBagestrclr = 1
#		GDBagestrfnt = fontS
	if GravDBDays <= GravDBDaysbad and GravDBPH2Days <= GravDBDaysbad:
		GDBagestr = "[✓] GDB PH1:{}d{}h PH2:{}d{}h".format(GravDBDays,GravDBHours,GravDBPH2Days,GravDBPH2Hours)
		GDBagestrclr = 1
		GDBagestrfnt = fontS
	elif GravDBDays > GravDBDaysbad:
		GDBagestr = "[✗] WARNING GDB Age PH2:{} days".format(GravDBDays)
		GDBagestrclr = 2
		GDBagestrfnt = fontL
	elif GravDBPH2Days > GravDBDaysbad:
		GDBagestr = "[✗] WARNING GDB Age PH1:{} days".format(GravDBDays)
		GDBagestrclr = 2
		GDBagestrfnt = fontL
	print(GDBagestr)

# GET IP ADDRESS
	try:
		ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
	except KeyError:
		ip_str = "[×] Can't connect to eth0"
		ip = ""
	if "192.168" in ip:
		ip_str = "[✓] IP of {}: {}".format(hostname, ip)

# Creates the different output lines based on above
	LINE1TXT = cputempstr
	LINE1CLR = cputempstrclr
	LINE1FNT = cputempstrfnt
	LINE2TXT = loadstr
	LINE2CLR = loadstrclr
	LINE2FNT = loadstrfnt
	LINE3TXT = GDBagestr
	LINE3CLR = GDBagestrclr
	LINE3FNT = GDBagestrfnt
	LINE4TXT = blockpstr
	LINE4CLR = blockpstrclr
	LINE4FNT = blockpstrfnt
	LINE5TXT = PHstatusstr
	LINE5CLR = PHstatusstrclr
	LINE5FNT = PHstatusstrfnt
#	OUTPUT_EXAMPLE = ip_str
#	OUTPUT_EXAMPLE = PHstatus[6].strip().replace('✗', '×')
#	OUTPUT_EXAMPLE = "[✓] There are {} clients connected".format(unique_clients)
#	OUTPUT_EXAMPLE = "[✓] Blocked {} objects".format(ads_blocked_today)
	draw_dashboard(LINE1TXT, LINE1CLR, LINE1FNT, LINE2TXT, LINE2CLR, LINE2FNT, LINE3TXT, LINE3CLR, LINE3FNT, LINE4TXT, LINE4CLR, LINE4FNT, LINE5TXT, LINE5CLR, LINE5FNT)
