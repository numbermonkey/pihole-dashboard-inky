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
import requests
import json
import os
import sys
import configparser
import netifaces as ni
import gpiozero as gz
from time import localtime, strftime
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from urllib.error import HTTPError, URLError

if os.geteuid() != 0:
    sys.exit("You need root permissions to access E-Ink display, try running with sudo!")

# This would be a neater way. Um.
# Read the config file
#parser = configparser.ConfigParser()
#parser.read('phdbinky.cfg')

# STATIC VARIABLES
INTERFACE = "eth0"
PIHOLE_PORT = 80
hostname = socket.gethostname() 
font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')
font_name = os.path.join(font_dir, "font.ttf")
fontL = ImageFont.truetype(font_name, 16)
fontM = ImageFont.truetype(font_name, 14)
fontS = ImageFont.truetype(font_name, 12)
#PH1 is a Pi-hole
PH1IPAddress = "192.168.1.86"
PH1Name = "PH2"
PH1apiPath = "/admin/api.php"
PH1apiURL = "http://{}:{}{}".format(PH1IPAddress,PIHOLE_PORT,PH1apiPath)
#PH2 is the other Pi-hole
PH2IPAddress = "192.168.1.87"
PH2Name = "PH3"
PH2apiPath = "/admin/api.php"
PH2apiURL = "http://{}:{}{}".format(PH2IPAddress,PIHOLE_PORT,PH2apiPath)
inkyWHITE = 0
inkyBLACK = 1
inkyRED = 2
DNSGoodCheck = "www.pi-hole.net"
PINGGoodCheck = "8.8.8.8"
PHGitHubURL = "https://github.com/pi-hole/pi-hole"
PHcmd = "/usr/local/bin/pihole"
URLtimeout = 0.5
t = strftime("%H:%M", localtime())
timestrtxt = "@ {}".format(t)
retrycount = 0
retrycountmax = 3

# Parameters for conditional text
cpucooltemp = 40.0  # Below this temparature is considered Cool
cpuoktemp = 65.0  # Below this temparature is considered OK but Warm
cpubadtemp = 80.0  # Below this temparature is Bad. Above is ELE.
loadhigh = 0.7  # 5 min cpu load in excess of 0.7 is high
utilhigh = 90.0  # A cpu utilisation %age of 90 is high
blockpbad = 0.1  # This is a bad blocked %age. This will trigger a warning if block% falls lower than this
GravDBDaysbad = 7  # Gravity database age over this is bad

# INKY SETUP
inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

def show(it):
	inky_display.set_image(it)
	inky_display.show()

def msg_send(title, content, priority):
	gotify_host = "192.168.1.85"
	gotify_port = 8180
	msg_token = "Aqdczwm4XyESN7I"
	gotify_url = "http://{}:{}/message?token={}".format(gotify_host, str(gotify_port), msg_token)
	resp = requests.post(gotify_url, json={
		"title": title,
		"message": content,
		"priority": priority
	})

# BIG RED BOX
def brb(alert):
	# Setup new image
	img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
	draw = ImageDraw.Draw(img)
	timestrclr = inkyWHITE
	timestrfnt = fontM
	timestrfntw, timestrfnth = timestrfnt.getsize(timestrtxt)
	# Draw time
	draw.text((1, (inky_display.HEIGHT - (timestrfnth + 2))), timestrtxt, timestrclr, timestrfnt)
	# Draw Big Red Box
	draw.rectangle([(0, 0), (inky_display.WIDTH, inky_display.HEIGHT)], fill=inkyRED)
	# Create centered alert text
	fatalstrtxt = alert
	fatalstrclr = inkyWHITE
	fatalstrfnt = fontM
	fatalstrfntw, fatalstrfnth = fatalstrfnt.getsize(fatalstrtxt)
	# Catch an error
	assert ((inky_display.WIDTH - fatalstrfntw) >0), "FONT WIDTH TOO BIG"
	assert ((inky_display.HEIGHT - fatalstrfnth) >0), "FONT HEIGHT TOO BIG"
	# Add alert text to image
	draw.text(((inky_display.WIDTH - fatalstrfntw) / 2, (inky_display.HEIGHT - fatalstrfnth) / 2) ,fatalstrtxt, fatalstrclr, fatalstrfnt)
	show(img)
	sys.exit("SERVER DOWN!")

# BASIC CHECK
def HostCheck(serverIP):
	response = subprocess.run(["ping", "-c", "3", serverIP],capture_output=False).returncode
	if response == 0:
		print (serverIP, 'is up!')
	else:
		warning = "{} is down!".format(serverIP)
		print (serverIP, 'is down!')
		msg_send(warning,"Alert by Dashboard at {}".format(timestrtxt), 8)
		brb(warning)

def InetCheck(public_site,retry,giveup):
	while retry <= giveup:
		response = subprocess.run(["ping", "-c", "3", public_site],capture_output=False).returncode
		if response == 0:
			print ('Broadband is up!')
			break
		else:
			retry = retry + 1
	if retry > giveup:
		warning = "Broadband is down!"
		print ('Broadband is down!')
		msg_send(warning,"Alert by Dashboard at {}".format(timestrtxt), 8)
		brb(warning)
	
InetCheck(PINGGoodCheck,retrycount,retrycountmax)
HostCheck(PH1IPAddress)
HostCheck(PH2IPAddress)

# Def draws 5 lines of text and a bottom bar. 
# Each needs 3 arguments: 
#				txt (content), 
#				clr (colour 0=White, 1=Black, 2=Red),
#				fnt (font - defined in static section)
# THIS DEF DRAWS THE FINAL SCREEN
def draw_dashboard(str1txt=None, str1clr=1, str1fnt=None, 
                   str2txt=None, str2clr=1, str2fnt=None, 
				   str3txt=None, str3clr=1, str3fnt=None, 
				   str4txt=None, str4clr=1, str4fnt=None, 
				   str5txt=None, str5clr=1, str5fnt=None):

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

#THESE SECTIONS DONT BELONG IN THE DRAW DEF

# GET VERSION
#Get local version as reported by Pi-Hole
	process = subprocess.run([PHcmd, "-v"], capture_output=True)
#Need to do some squirrely text manipulation
	output = process.stdout.decode()
	if "Pi-hole" in output:
		lclchar = output.index('v',19) # 19 to miss the first v in version
		lclverstr = output[lclchar+1:lclchar+6] # I want 5 characters. Do they write major versions with the .0s I wonder? They do not. NEEDS FIXING.
		lclverint = int(''.join(i for i in lclverstr if i.isdigit()))
		if lclverint < 100:
			lclverint = lclverint * 10
			lclverstr = lclverstr[0:3]
	else:
		lclverstr = "0.0.0"
		lclverint = 0
#Next section broken since git hub doesnt list latest version last. i.e. v5.2 > 5.10 which is wrong.
#Need to rethink how to compare local ver to repo ver
#Now get Github repository version by reading last tag.
#	process = subprocess.run(["git", "ls-remote", "--tags", PHGitHubURL], capture_output=True)
#	process = subprocess.run(["git", "ls-remote", "--tags", PHGitHubURL, "|", "grep", "-o", "'v.*'", "|", "sort", "-V"], capture_output=True)
#	output = process.stdout.decode()
#	output = process.stdout.read().decode().splitlines()[-1:]
#	git ls-remote --tags https://github.com/pi-hole/pi-hole | grep -o 'v.*' | sort -V <-- WORKS!!
#	if not "fatal" in process.stderr.decode():
#		repoverstr = process.stdout.decode()[-6:].rstrip() <--Maybe work out where the last v is? v5.10 is only 5 chars. Is asking for 6 tripping it up?
#		repoverint = int(''.join(i for i in repoverstr if i.isdigit())) <-- FAILS HERE??
#		if repoverint < 100:
#			repoverint = repoverint * 10
#			repoverstr = repoverstr[-3:]
#	else:
#		repoverstr = "0.0.0"
#		repoverint = 0
##Build the string
#	if (lclverint == repoverint != 0):
	boxclr = inkyBLACK
	verstrtxt = "{} version is v{}".format(PH1Name, lclverstr)
	verstrfnt = timestrfnt = fontS
	verstrclr = timestrclr = inkyWHITE
#	elif repoverint > lclverint:
#		if lclverint == 0:
#			boxclr = inkyRED
#			verstrtxt = "[✗] Error getting local ver"
#			verstrfnt = timestrfnt = fontM
#			verstrclr = timestrclr = inkyWHITE
#			msg_send("VERSION ERROR",verstrtxt,4)
#		else:
#			boxclr = inkyRED
#			verstrtxt = "[✗] UPDATE v{}".format(repoverstr)
#			verstrfnt = timestrfnt = fontL
#			verstrclr = timestrclr = inkyWHITE
#			msg_send("UPDATE AVAILABLE",verstrtxt,4)
#	else:
#		if repoverint == 0:
#			boxclr = inkyRED
#			verstrtxt = "[✗] Error getting repo ver"
#			verstrfnt = timestrfnt = fontM
#			verstrclr = timestrclr = inkyWHITE
#			msg_send("VERSION ERROR",verstrtxt,4)
#		else:
#			boxclr = inkyRED
#			verstrtxt = "[✗] REPO IS EARLIER ?? {}".format(repoverstr)
#			verstrfnt = timestrfnt = fontL
#			verstrclr = timestrclr = inkyWHITE
#			msg_send("WEIRD ERROR",verstrtxt,8)
	print(verstrtxt,"  ",timestrtxt)
# Measures width & height of text used for bar given font size
	verstrfntw, verstrfnth = verstrfnt.getsize(verstrtxt)
	timestrfntw, timestrfnth = timestrfnt.getsize(timestrtxt)
# Calculates box dimension based on font height
	toprightcornery = inky_display.HEIGHT - verstrfnth - 1
	assert (toprightcornery >=0), "ERR..SOMETHING WRONG DETERMINING TOP CORNER OF BOTTOM BOX. FONT TOO LARGE?"
	draw.rectangle([(0, toprightcornery), (inky_display.WIDTH, inky_display.HEIGHT+1)], fill=boxclr)
# Adds version and time to bottom box. 
	boxtxtindent = 5
	draw.text((boxtxtindent,toprightcornery), verstrtxt, verstrclr, verstrfnt)
	draw.text((inky_display.WIDTH - timestrfntw - boxtxtindent,toprightcornery), timestrtxt, timestrclr, timestrfnt)
# Send to Inky
	show(img)

def update():

# THIS DEF UPDATES ALL THE STATS
# REMOTE STATS
# Read the PH api values
# Check to make sure web server is reachable and api page is up
	PH1URLcheck = urllib.request.urlopen(PH1apiURL,timeout=URLtimeout).getcode()
	if PH1URLcheck != 200:
		PH1URLstatus = "down"
	else:
		PH1URLstatus = "up"
		PH1URLpage = urllib.request.urlopen(PH1apiURL,timeout=URLtimeout).read().decode()
		if not 'Did you mean to go to the admin panel?' in PH1URLpage:
			PH1stats = json.load(urllib.request.urlopen(PH1apiURL,timeout=URLtimeout))
		else:
			PH1URLstatus = "down"

	PH2URLcheck = urllib.request.urlopen(PH2apiURL,timeout=URLtimeout).status
#	PH2URLcheck = urllib.request.urlopen(PH2apiURL,timeout=URLtimeout).getcode()
	if PH2URLcheck != 200:
		PH2URLstatus = "down"
	else:
		PH2URLstatus = "up"
		PH2URLpage = urllib.request.urlopen(PH2apiURL,timeout=URLtimeout).read().decode()
		if not 'Did you mean to go to the admin panel?' in PH2URLpage:
			PH2stats = json.load(urllib.request.urlopen(PH2apiURL,timeout=URLtimeout))
		else:
			PH2URLstatus = "down"

# REMOTE STATS
# GET PIHOLE STATUS & DNS RESOLUTION STATUS
# Use api JSON get PI-hole reported status
	if PH1URLstatus == "up":
		PH1ReportedStatus = PH1stats['status']
	else:
		PH1ReportedStatus = "{} URL Down".format(PH1Name)
	if PH2URLstatus == "up":
		PH2ReportedStatus = PH2stats['status']
	else:
		PH2ReportedStatus = "{} URL Down".format(PH2Name)
# Get actual DNS status through dig probe
	if "NOERROR" in subprocess.check_output(["dig", DNSGoodCheck, "@" + PH1IPAddress]).decode():
		PH1DNSStatus = "enabled"
	else:
		PH1DNSStatus = "dnsdown"
	if "NOERROR" in subprocess.check_output(["dig", DNSGoodCheck, "@" + PH2IPAddress]).decode():
		PH2DNSStatus = "enabled"
	else:
		PH2DNSStatus = "dnsdown"	

# Conditions for Status text output
	if PH1ReportedStatus == PH2ReportedStatus == PH1DNSStatus == PH2DNSStatus == "enabled":
		PHStatusstrtxt = "[✓] Status {}:[✓] {}:[✓]".format(PH1Name , PH2Name)
		PHStatusstrtxtclr = inkyBLACK
		PHStatusstrtxtfnt = fontS
	elif PH2ReportedStatus != PH2DNSStatus:
		if PH2ReportedStatus != "enabled":
			PHStatusstrtxt = "[✗]{} PH:[✗] DNS:[✓]".format(PH2Name)
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontM
			msg_send("{} Problem",PHStatusstrtxt, 8).format(PH2Name)
		else:
			PHStatusstrtxt = "[✗]{} PH:[✓] DNS:[✗]".format(PH2Name)
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontM
			msg_send("{} Problem",PHStatusstrtxt, 8).format(PH2Name)
	elif PH1ReportedStatus != PH1DNSStatus:
		if PH1ReportedStatus != "enabled":
			PHStatusstrtxt = "[✗]{} PH:[✗] DNS:[✓]".format(PH1Name)
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontM
			msg_send("{} Problem",PHStatusstrtxt, 8).format(PH1Name)
		else:
			PHStatusstrtxt = "[✗]{} PH:[✓] DNS:[✗]".format(PH1Name)
			PHStatusstrtxtclr = inkyRED
			PHStatusstrtxtfnt = fontM
			msg_send("{} Problem",PHStatusstrtxt, 8).format(PH1Name)
	else:
		PHStatusstrtxt = " [✗] [✗] AWOOGA !! [✗] [✗]"
		PHStatusstrtxtclr = inkyRED
		PHStatusstrtxtfnt = fontL
		msg_send("WHEELS OFF!",PHStatusstrtxt,8)
		
# Moved print(PHStatusstrtxt) down to better emulate display in run-time terminal output

# REMOTE STATS
# GET PIHOLE STATISTICS
# First for 1st PH. Uses api JSON
	if PH1URLstatus == "up": 
		PH1unique_clients = PH1stats['unique_clients']
		PH1ads_blocked_today = PH1stats['ads_blocked_today']
		PH1blockp = round(PH1stats['ads_percentage_today'],1)
		PH1GravDBDays = PH1stats['gravity_last_updated']['relative']['days']
		PH1GravDBHours = PH1stats['gravity_last_updated']['relative']['hours']
	else:
		PH1blockp = 0
		PH1GravDBDays = GravDBDaysbad + 1
		PH1GravDBHours = 0
# Then for 2nd PH. Uses api JSON
	if PH2URLstatus == "up":
		PH2unique_clients2 = PH2stats['unique_clients']
		PH2ads_blocked_today = PH2stats['ads_blocked_today']
		PH2blockp = round(PH2stats['ads_percentage_today'],1)
		PH2GravDBDays = PH2stats['gravity_last_updated']['relative']['days']
		PH2GravDBHours = PH2stats['gravity_last_updated']['relative']['hours']
	else:
		PH2blockp = 0
		PH2GravDBDays = GravDBDaysbad + 1
		PH2GravDBHours = 0

# Conditions for Block% text output
	if PH1blockp > blockpbad and PH2blockp > blockpbad and (PH1blockp + PH2blockp) !=0:
		blockpstr = "[✓] {}: {}%  {}: {}%".format(PH1Name,PH1blockp,PH2Name,PH2blockp) 
		blockpstrclr = inkyBLACK
		blockpstrfnt = fontS
	elif PH1blockp <= blockpbad:
		blockpstr = "[✗] ALERT Block % {}:{}".format(PH1Name,PH1blockp)
		blockpstrclr = inkyRED
		blockpstrfnt = fontL
		msg_send("BLOCKING PROBLEM?",blockpstr,4)
	elif PH2blockp <= blockpbad:
		blockpstr = "[✗] ALERT Block % {}:{}".format(PH2Name,PH2blockp)
		blockpstrclr = inkyRED
		blockpstrfnt = fontL
		msg_send("BLOCKING PROBLEM?",blockpstr,4)
	print(blockpstr)
	print(PHStatusstrtxt)

# Conditions for GravDB age text output
	if PH1GravDBDays <= GravDBDaysbad and PH2GravDBDays <= GravDBDaysbad:
		GDBagestr = "[✓] GDB {}:{}d{}h {}:{}d{}h".format(PH1Name,PH1GravDBDays,PH1GravDBHours,PH2Name,PH2GravDBDays,PH2GravDBHours)
		GDBagestrclr = inkyBLACK
		GDBagestrfnt = fontS
	elif PH1GravDBDays > GravDBDaysbad:
		GDBagestr = "[✗] GDB Age {}:{} days".format(PH1Name,PH1GravDBDays)
		GDBagestrclr = inkyRED
		GDBagestrfnt = fontM
	elif PH2GravDBDays > GravDBDaysbad:
		GDBagestr = "[✗] GDB Age {}:{} days".format(PH2Name,PH2GravDBDays)
		GDBagestrclr = inkyRED
		GDBagestrfnt = fontM
	print(GDBagestr)

# LOCAL STAT
# GET IP ADDRESS
	try:
		ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
	except KeyError:
		ip_str = "[×] Can't connect to {}".format(INTERFACE)
		ip = ""
	if "192.168" in ip:
		ip_str = "[✓] IP of {}: {}".format(hostname, ip)
		ip_clr = inkyBLACK
		ip_fnt = fontS
	else:
		ip_str = "[×] Can't get local address"
		ip_clr = inkyRED
		ip_fnt = fontL
# LOCAL STAT
# GET TEMPERATURE
# Query Local GPIO for the temperature
	cpu_temp = gz.CPUTemperature().temperature
	cpu_temp = round(cpu_temp, 1)
# Conditions for Temp text output
	if cpu_temp <= cpucooltemp:
		cputempstr = "[✓] Cool {}C".format(cpu_temp)
		cputempstrclr = inkyBLACK
		cputempstrfnt = fontS
	elif cpu_temp > cpucooltemp <= cpuoktemp:
		cputempstr = "[✓] Warm {}".format(cpu_temp)
		cputempstrclr = inkyBLACK
		cputempstrfnt = fontM
		msg_send("WARM",cputempstr,4)
	elif cpu_temp > cpuoktemp <= cpubadtemp:
		cputempstr = "[✗] WARNING {}".format(cpu_temp)
		cputempstrclr = inkyRED
		cputempstrfnt = fontL
		msg_send("WARNING",cputempstr,8)
	elif cpu_temp > cpubadtemp:
		cputempstr = "[✗] DANGER {}".format(cpu_temp)
		cputempstrclr = inkyRED
		cputempstrfnt = fontL
		msg_send("DANGER",cputempstr,8)
	print(cputempstr)

# LOCAL STAT
# GET LOAD
# Get Load 5 min from uptime
	cmd = "/usr/bin/uptime"
	process = subprocess.Popen(cmd.split(','), stdout=subprocess.PIPE)
	output = process.stdout.read().decode().split(",")
	load5min = float(output[-2])
# Get CPU %age from stat
#	last_idle = last_total = 0
	with open('/proc/stat') as f:
		fields = [float(column) for column in f.readline().strip().split()[1:]]
		idle, total = fields[3], sum(fields)
#	idle_delta, total_delta = idle - last_idle, total - last_total
#	utilisation = 100.0 * (1.0 - idle_delta / total_delta)
	utilisation = 100.0 * (1.0 - idle / total)
	utilisation = round(utilisation, 1)
# Conditions for Load text output
	if load5min < loadhigh:
		loadstr = "[✓] [✓]: {} at CPU: {}%".format(load5min,utilisation)
		loadstrclr = inkyBLACK
		loadstrfnt = fontS
	elif load5min >= loadhigh and utilisation < utilhigh:
		loadstr = "[✗] WRKN:{} at CPU:{}%".format(load5min,utilisation)
		loadstrclr = inkyBLACK
		loadstrfnt = fontM
	elif load5min >= loadhigh and utilisation >= utilhigh:
		loadstr = "[✗] DANGER {} at CPU:{}%".format(load5min,utilisation)
		loadstrclr = inkyRED
		loadstrfnt = fontL
		msg_send("LOAD HIGH",loadstr,8)
	print(loadstr)

# Creates the different output lines based on above
# TUP is str, clr, fnt
	LINE1TXT = cputempstr
	LINE1CLR = cputempstrclr
	LINE1FNT = cputempstrfnt
	LINE1TUP = (LINE1TXT, LINE1CLR, LINE1FNT)
#	LINE1TUP = (cputempstr,cputempstrclr,cputempfnt)
	LINE2TXT = loadstr
	LINE2CLR = loadstrclr
	LINE2FNT = loadstrfnt
	LINE2TUP = (LINE2TXT, LINE2CLR, LINE2FNT)
#	LINE2TUP = (loadstr,loadstrclr,loadstrfnt)
	LINE3TXT = GDBagestr
	LINE3CLR = GDBagestrclr
	LINE3FNT = GDBagestrfnt
#	LINE3TUP = (LINE3TXT, LINE3CLR, LINE3FNT)
	LINE4TXT = blockpstr
	LINE4CLR = blockpstrclr
	LINE4FNT = blockpstrfnt
#	LINE4TUP = (LINE4TXT, LINE1CLR, LINE1FNT)
	LINE5TXT = PHStatusstrtxt
	LINE5CLR = PHStatusstrtxtclr
	LINE5FNT = PHStatusstrtxtfnt
#	LINE5TUP = (LINE5TXT, LINE5CLR, LINE5FNT)
#	OUTPUT_EXAMPLE = ip_str
#	OUTPUT_EXAMPLE = PH1ReportedStatus[6].strip().replace('✗', '×')
#	OUTPUT_EXAMPLE = "[✓] There are {} clients connected".format(unique_clients)
#	OUTPUT_EXAMPLE = "[✓] Blocked {} objects".format(ads_blocked_today)
	draw_dashboard(LINE1TXT, LINE1CLR, LINE1FNT, LINE2TXT, LINE2CLR, LINE2FNT, LINE3TXT, LINE3CLR, LINE3FNT, LINE4TXT, LINE4CLR, LINE4FNT, LINE5TXT, LINE5CLR, LINE5FNT)
#	draw_dashboard(LINE1TUP,LINE2TUP,LINE3TUP,LINE4TUP,LINE5TUP)