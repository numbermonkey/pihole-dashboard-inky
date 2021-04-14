#!/usr/bin/env python3

# pihole-dashboard-inky
# Copyright (C) 2021  santoru
# modified for inky RED by numbermonkey
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
#
# Inky Colours
# 0 = WHITE
# 1 = BLACK
# 2 = RED

import subprocess
import socket
import urllib.request
import json
import os
import sys
#import re
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
hostname = socket.gethostname() # Err..not a var
font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')  # Err..not a var
font_name = os.path.join(font_dir, "font.ttf")  # Err..not a var
fontL = ImageFont.truetype(font_name, 16)
fontS = ImageFont.truetype(font_name, 12)
PHIPAddress = "192.168.1.86"
PHapiURL = "http://127.0.0.1:{}/admin/api.php".format(PIHOLE_PORT)
PH2IPAddress = "192.168.1.85"
PH2apiURL = "http://192.168.1.85:{}/admin/api.php".format(PIHOLE_PORT)
inkyWHITE = 0
inkyBLACK = 1
inkyRED = 2
DNSGoodCheck = "www.pi-hole.net"
PHGitHubURL = "https://github.com/pi-hole/pi-hole"
PHcmd = "/usr/local/bin/pihole"

# Parameters for conditional text
cpucooltemp = 40.0
cpuoktemp = 65.0
cpubadtemp = 80.0
loadhigh = 0.7
utilhigh = 90.0
blockpbad = 0.0
GravDBDaysbad = 5
	
# INKY SETUP
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

# Def draws 6 lines of text. Each needs 3 arguments: txt (content), clr (colour 0=White, 1=Black, 2=Red) ,fnt (font - defined in static section)
def draw_dashboard(str1txt=None, str1clr=1, str1fnt=None, 
                   str2txt=None, str2clr=1, str2fnt=None, 
				   str3txt=None, str3clr=1, str3fnt=None, 
				   str4txt=None, str4clr=1, str4fnt=None, 
				   str5txt=None, str5clr=1, str5fnt=None):

# THIS DEF DRAWS THE FINAL SCREEN
# Get Time
	t = strftime("%H:%M", localtime())
	timestrtxt = "@ {}".format(t)
# Get Version
#Get local version as reported by Pi-Hole
	cmd = PHcmd
	process = subprocess.run([cmd, "-v"], capture_output=True)
#Need to do some squirrely text manipulation
	output = process.stdout.decode()
	if "Pi-hole" in output:
		char = output.index('v',11) # 11 to miss the first v in version
		lclver = output[char+1:char+6]
		lclverint = ''.join(i for i in lclver if i.isdigit())
	else:
		lclver = "0.0.0"
		lclverint = 0
# Now get Github repository version by reading last tag.
	process = subprocess.run(["git", "ls-remote", "--tags", PHGitHubURL], capture_output=True)
	output = process.stdout.decode()
	if not "fatal" in output:
		repover = process.stdout.decode()[-6:].rstrip()
		repoverint = ''.join(i for i in repover if i.isdigit())
	else:
		repover = "0.0.0"
		repoverint = 0
#Build the string
	if lclverint == repoverint != 0:
			boxclr = inkyBLACK
			verstrtxt = "Pi-hole version is v{}".format(lclver)
			verstrfnt = timestrfnt = fontS
			verstrclr = timestrclr = inkyWHITE
	elif repoverint > lclverint:
		if lclverint == 0:
			boxclr = inkyRED
			verstrtxt = "[✗] Error getting local ver"
			verstrfnt = timestrfnt = fontL
			verstrclr = timestrclr = inkyWHITE
		else:
			boxclr = inkyRED
			verstrtxt = "[✗] UPDATE AVAILABLE {}".format(repover)
			verstrfnt = timestrfnt = fontL
			verstrclr = timestrclr = inkyWHITE
	else:
		if repoverint == 0:
			boxclr = inkyRED
			verstrtxt = "[✗] Error getting repository ver"
			verstrfnt = timestrfnt = fontL
			verstrclr = timestrclr = inkyWHITE
		else:
			boxclr = inkyRED
			verstrtxt = "[✗] REPO IS EARLIER VER ?? {}".format(repover)
			verstrfnt = timestrfnt = fontL
			verstrclr = timestrclr = inkyWHITE
	print(verstrtxt,"  ",timestrtxt)
# Init screen	
	img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
	draw = ImageDraw.Draw(img)
# Draws the text lines as long as parameters are passed to it
	if not None in {str1txt, str2txt, str3txt, str4txt, str5txt}:
# gap from top and indent
		drop = 1
		indent = 1
# draws the str txts and allows 1 line between them. Uses height of font to determine gap		
		draw.text((indent,drop),str1txt, str1clr, str1fnt)
		w, h = str1fnt.getsize(str1txt)
		drop = drop + h + 1
		draw.text((indent,drop),str2txt, str2clr, str2fnt)
		w, h = str2fnt.getsize(str2txt)
		drop = drop + h + 1
		draw.text((indent,drop),str3txt, str3clr, str3fnt)
		w, h = str3fnt.getsize(str3txt)
		drop = drop + h + 1
		draw.text((indent,drop),str4txt, str4clr, str4fnt)
		w, h = str4fnt.getsize(str4txt)
		drop = drop + h + 1
		draw.text((indent,drop),str5txt, str5clr, str5fnt)
# Rectangle at bottom
# Measures height of font used for version text
	verstrfntw, verstrfnth = verstrfnt.getsize(verstrtxt)
# Calculates box dimension based on font height
	toprightcorner = inky_display.HEIGHT - verstrfnth - 1
	assert (toprightcorner >=0), "ERR..SOMETHING WRONG DETERMINING TOP CORNER. FONT TOO LARGE?"
	draw.rectangle([(0, toprightcorner), (inky_display.WIDTH, inky_display.HEIGHT+1)], fill=boxclr)
	print(toprightcorner)
# Adds version and time to bottom box. 		
	draw.text((5,toprightcorner), verstrtxt, verstrclr, verstrfnt)
	draw.text((150,toprightcorner), timestrtxt, timestrclr, timestrfnt)
# Send to Inky
	inky_display.set_image(img)
	inky_display.show()

def update():

# THIS DEF UPDATES THE TEXT LINES
# Read the PH api values
#WRAP THIS IN TRY	
	PHstats = json.load(urllib.request.urlopen(PHapiURL))
	PH2stats = json.load(urllib.request.urlopen(PH2apiURL))
# GET TEMPERATURE
# Query GPIO for the temperature
	cpu_temp = gz.CPUTemperature().temperature
	cpu_temp = round(cpu_temp, 1)
# Conditions for text output
	if cpu_temp <= cpucooltemp:
		cputempstr = "[✓] Cool {}C".format(cpu_temp)
		cputempstrclr = inkyBLACK
		cputempstrfnt = fontS
	elif cpu_temp > cpucooltemp <= cpuoktemp:
		cputempstr = "[✓] Warm {}".format(cpu_temp)
		cputempstrclr = inkyBLACK
		cputempstrfnt = fontL
	elif cpu_temp > cpuoktemp <= cpubadtemp:
		cputempstr = "[✗] WARNING {}".format(cpu_temp)
		cputempstrclr = inkyRED
		cputempstrfnt = fontL
	elif cpu_temp > cpubadtemp:
		cputempstr = "[✗] DANGER {}".format(cpu_temp)
		cputempstrclr = inkyRED
		cputempstrfnt = fontL
	print(cputempstr)

# GET LOAD
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
#	last_idle, last_total = idle, total
# Conditions for text output
	if load5min < loadhigh:
		loadstr = "[✓] Load: {} at CPU: {}%".format(load5min,utilisation)
		loadstrclr = inkyBLACK
		loadstrfnt = fontS
	elif load5min >= loadhigh and utilisation < utilhigh:
		loadstr = "[✗] Load:{} CPU:{}%".format(load5min,utilisation)
		loadstrclr = inkyRED
		loadstrfnt = fontL
	elif load5min >= loadhigh and utilisation >= utilhigh:
		loadstr = "[✗] DANGER Load:{} CPU:{}%".format(load5min,utilisation)
		loadstrclr = inkyRED
		loadstrfnt = fontL
	print(loadstr)

# GET PIHOLE STATUS
# Use api JSON get PI-Hole reported status
	PHReportedStatus = PHstats['status']
	PH2ReportedStatus = PH2stats['status']
# Get actual DNS status through dig probe
	if "NOERROR" in subprocess.check_output(["dig", DNSGoodCheck, "@" + PHIPAddress]).decode():
		PHDNSStatus = "enabled"
	else:
		PHDNSStatus = "dnsdown"
	if "NOERROR" in subprocess.check_output(["dig", DNSGoodCheck, "@" + PH2IPAddress]).decode():
		PH2DNSStatus = "enabled"
	else:
		PH2DNSStatus = "dnsdown"	
# Conditions for text output
	if PHReportedStatus == PH2ReportedStatus == PHDNSStatus == PH2DNSStatus == "enabled":
		PHStatusstrtxt = "[✓] Status PH1:[✓] PH2:[✓]"
		PHStatusstrtxtclr = inkyBLACK
		PHStatusstrtxtfnt = fontS
	elif PH2ReportedStatus != PH2DNSStatus:
		if PH2ReportedStatus != "enabled":
			PHStatusstrtxt = "[✗]PH1 PH:[✗] DNS:[✓]"
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontL
		else:
			PHStatusstrtxt = "[✗]PH1 PH:[✓] DNS:[✗]"
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontL
	elif PHReportedStatus != PHDNSStatus:
		if PHReportedStatus != "enabled":
			PHStatusstrtxt = "[✗]PH2 PH:[✗] DNS:[✓]"
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontL
		else:
			PHStatusstrtxt = "[✗]PH2 PH:[✓] DNS:[✗]"
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontL
	else:
		PHStatusstrtxt = " [✗] [✗] AWOOGA !! [✗] [✗]"
		PHStatusstrtxtclr = inkyRED
		PHStatusstrtxtfnt = fontL
		
# Moved print(PHStatusstrtxt) down to better emulate display

# GET PIHOLE STATISTICS
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
		blockpstrclr = inkyBLACK
		blockpstrfnt = fontS
	elif blockp <= blockpbad:
		blockpstr = "[✗] DANGER Block % PH2:{}".format(blockp)
		blockpstrclr = inkyRED
		blockpstrfnt = fontL
	elif blockpPH2 <= blockpbad:
		blockpstr = "[✗] DANGER Block % PH1:{}".format(blockpPH2)
		blockpstrclr = inkyRED
		blockpstrfnt = fontL
	print(blockpstr)
	print(PHStatusstrtxt)

# GET GRAVITY AGE
# First for local PH. Uses api JSON
	PHGravDBDays = PHstats['gravity_last_updated']['relative']['days']
	PHGravDBHours = PHstats['gravity_last_updated']['relative']['hours']
# Then for 2nd PH. Uses api JSON
	PH2GravDBDays = PH2stats['gravity_last_updated']['relative']['days']
	PH2GravDBHours = PH2stats['gravity_last_updated']['relative']['hours']
# Conditions for text output
	if PHGravDBDays <= GravDBDaysbad and PH2GravDBDays <= GravDBDaysbad:
		GDBagestr = "[✓] GDB PH1:{}d{}h PH2:{}d{}h".format(PH2GravDBDays,PH2GravDBHours,PHGravDBDays,PHGravDBHours)
		GDBagestrclr = inkyBLACK
		GDBagestrfnt = fontS
	elif PHGravDBDays > GravDBDaysbad:
		GDBagestr = "[✗] WARNING GDB Age PH2:{} days".format(PHGravDBDays)
		GDBagestrclr = inkyBLACK
		GDBagestrfnt = fontL
	elif PH2GravDBDays > GravDBDaysbad:
		GDBagestr = "[✗] WARNING GDB Age PH1:{} days".format(PH2GravDBDays)
		GDBagestrclr = inkyRED
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
	LINE5TXT = PHStatusstrtxt
	LINE5CLR = PHStatusstrtxtclr
	LINE5FNT = PHStatusstrtxtfnt
#	OUTPUT_EXAMPLE = ip_str
#	OUTPUT_EXAMPLE = PHReportedStatus[6].strip().replace('✗', '×')
#	OUTPUT_EXAMPLE = "[✓] There are {} clients connected".format(unique_clients)
#	OUTPUT_EXAMPLE = "[✓] Blocked {} objects".format(ads_blocked_today)
	draw_dashboard(LINE1TXT, LINE1CLR, LINE1FNT, LINE2TXT, LINE2CLR, LINE2FNT, LINE3TXT, LINE3CLR, LINE3FNT, LINE4TXT, LINE4CLR, LINE4FNT, LINE5TXT, LINE5CLR, LINE5FNT)
