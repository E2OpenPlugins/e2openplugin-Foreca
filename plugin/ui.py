# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from . import _  # , file_url

from Components.AVSwitch import AVSwitch
from Components.ActionMap import HelpableActionMap
from Components.ConfigList import ConfigList
from Components.ConfigList import ConfigListScreen
from Components.GUIComponent import GUIComponent
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.Sources.StaticText import StaticText
from Components.config import (
	config,
	configfile,
	ConfigSelection,
	ConfigInteger,
	ConfigYesNo,
	ConfigEnableDisable,
	getConfigListEntry,
	KEY_LEFT,
	KEY_RIGHT,
	KEY_0,
	ConfigText,
)
from datetime import timedelta
from enigma import (
	eListboxPythonMultiContent,
	ePicLoad,
	eTimer,
	getDesktop,
	gFont,
	RT_VALIGN_CENTER,
)
from json import loads
from locale import setlocale, LC_COLLATE
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CONFIG, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from os import makedirs, unlink, remove, listdir
from os.path import exists, join, getsize
from re import sub, DOTALL, findall
from skin import parseFont, parseColor
from sys import version_info
from twisted.internet._sslverify import ClientTLSOptions
from twisted.internet.reactor import callInThread
from twisted.internet.ssl import ClientContextFactory
import ssl

PY3 = version_info[0] == 3
if PY3:
	from urllib.request import urlopen, Request, pathname2url
else:
	from urllib import pathname2url
	from urllib2 import urlopen, Request


try:
	from urllib.parse import urlparse
except ImportError:
	from urlparse import urlparse


# try:
	# from PIL import Image
# except ImportError:
	# from Image import Image


try:
	_create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
	pass
else:
	ssl._create_default_https_context = _create_unverified_https_context


try:
	unicode
except NameError:
	unicode = str

VERSION = "3.3.9"


#
#  $Id$
#
# -------------------------------------------------------
#
#              Foreca Weather Forecast E2
#
#   This Plugin retrieves the actual weather forecast
#   for the next 10 days from the Foreca website.
#
#        We wish all users wonderful weather!
#
#
#                 11/03/2025
#
#     Source of information: https://www.foreca.ba
#
#             Design and idea by
#                  @Bauernbub
#            enigma2 mod by mogli123
#
# -------------------------------------------------------
#
#  Provided with no warranties of any sort.
#
# -------------------------------------------------------
#
# History:
# 2.6 Various minor changes
# 2.7 Wrap around mode enabled in screen-lists
# 2.8 Calculate next date based on displayed date when left/right key is pushed
#     after prior date jump using 0 - 9 keys was performed
# 2.9 Fix: Show correct date and time in weather videos
#     Main screen navigation modified to comply with standard usage:
#     scroll page up/down by left/right key
#     select previous/next day by left/right arrow key of numeric key group
# 2.9.1 Latvian cities and localization added. Thanks to muca
# 2.9.2 Iranian cities updated and localization added. Thanks to Persian Prince
#   Hungarian and Slovakian cities added. Thanks to torpe
# 2.9.3 Detail line in main screen condensed to show more text in SD screen
#   Grading of temperature colors reworked
#   Some code cosmetics
#   Translation code simplified: Setting the os LANGUAGE variable isn't needed anymore
#   Typos in German localization fixed
# 2.9.4 Many world-wide cities added. Thanks to AnodA
#   Hungarian and Slovakian localization added. Thanks to torpe
# 2.9.5 Fixed: Cities containing "_" didn't work as favorites. Thanks to kashmir
# 2.9.6 Size of temperature item slightly extended to match with skins using italic font
#   Grading of temperature colors reworked
# 2.9.7 Use specified "Frame size in full view" value when showing "5 day forecast" chart
#   Info screen reworked
#   False temperature colors fixed
#   Up/down keys now scroll by page in main screen (without highlighting selection)
# 3.0.0 Option added to select measurement units. Thanks to muca
#   Option added to select time format.
#   Setup menu reworked.
#   Main screen navigation modified: Select previous/next day by left/right key
#   Many Italian cities added and Italian localization updated. Thanks to mat8861
#   Czech, Greek, French, Latvian, Dutch, Polish, Russian localization updated. Thanks to muca
# 3.0.1 Fix broken transliteration
#   Disable selection in main screen.
# 3.0.2 Weather maps of Czech Republic, Greece, Hungary, Latvia, Poland, Russia, Slovakia added
#   Temperature Satellite video added
#   Control key assignment in slide show reworked to comply with Media Player standard
#   Some Italian cities added
#   Thumbnail folders compacted
#   Unused code removed, redundant code purged
#   Localization updated
# 3.0.3 List of German states and list of European countries sorted
#   Code cosmetics
#   Localization updated
# 3.0.4 Language determination improved
# 3.0.5 Setup of collating sequence reworked
# 3.0.6 Weather data in Russian version obtained from foreca.com instead of foreca.ru due
#     to structural discrepancy of Russian web site
#   Code cosmetics
# 3.0.7 Turkish cities updated. Thanks to atsiz77
#   Debug state noted in log file
# 3.0.8 Fixed for Foreca's pages changes
# 3.0.9 Path for weather map regions updated after change of Wetterkontor's pages. Thanks to Bag58.
#   Add missing spinner icon
# 3.1.0 Plugin splitted into a loader and UI part, as Foreca needs quite a while to load. Hence
#     actual load postponed until the user requests for it.
#   Finnish localization added. Thanks to kjuntara
#   Ukrainian localization added. Thanks to Irkoff
# 3.1.1 ForecaPreview skineable
# 3.1.2 Next screens skineable
# 3.1.3 Added font size for slideshow into setting
# 3.1.4 rem /www.metoffice.gov.uk due non existing infrared on this pages more
# 3.1.7 fix url foreca com
# 3.1.8 fix problem with national chars in favorite names
# 3.1.9 renamed parsed variables, added humidity into list - for display in default screen must be:
#   changed line:       self.itemHeight = 90   ... change to new height, if is needed
#   and rearanged lines:    self.valText1 = 365,5,600,28
#               self.valText2 = 365,33,600,28
#               self.valText3 = 365,59,600,28
#               self.valText4 = 365,87,600,28
#   similar in user skin - there text4Pos="x,y,w,h" must be added
# 3.2.0 fixed satellite maps, removed infrared - page not exist more, sanity check if nothing is downloaded
# 3.2.3-r3 change URL to .net and .ru
# 3.2.7 change URL to .hr, Py3-bugfix for videos and several code cleanups
# 3.2.8 'startservice.cfg', 'fav1.cfg' and 'fav2.cfg' are obsolete and now part of etc/enigma2/settings and therefore can be deleted
# 3.2.9 change URL to .biz (THX to jup @OpenA.TV) and some code improvements
#
# To do:
#   Add 10 day forecast on green key press
#   City search at Foreca website on yellow key press. This will eliminate complete city DB.
#   Option to add unlimited cities to a favorite list and to manage this favorite list (add & delete city, sort list).
#   Show home city (first entry of favorite list) on OK key press.
#   Skip to next/previous favorite city on left/right arrow key.
#   Show weather videos and maps on blue key
#   Show setup menu on Menu key
# 3.2.11 Umstellung auf Foreca Seite .biz und Nutzung WebClientContextFactory für https
# Unresolved: Crash when scrolling in help screen of city panel
# To do:
#   Show weather videos and maps on blue key
#   Show setup menu on Menu key
#
# 3.3.4 change URL to and many code improvements
#  RECODE FROM LULULLA TO 20241222
# To do:
#   Add choice list for pressur and other menu
#   check all url and fetch..
#   CACHE_PATH moved
#   FAlog moved
#   secure remove image from folde CACHE_PATH
#   Remove profile ICC from bad image
# 3.3.5 change URL to and many code improvements
#  RECODE FROM LULULLA
# To do:
#   Add server url online
# 3.3.6 fix translations and many code improvements
#  RECODE FROM LULULLA
# 3.3.7 removed .cfg files - add TV button for Menu Config
#  RECODE FROM LULULLA
# 3.3.8 Mahor fix on clean all code unnecessay / append new PY3
#  Translate 90% complete
#  # thank's Orlandoxx  restore Eumsat screen picxview
#  RECODE FROM LULULLA
# 3.3.9  fixed


class WebClientContextFactory(ClientContextFactory):
	def __init__(self, url=None):
		domain = urlparse(url).netloc
		self.hostname = domain

	def getContext(self, hostname=None, port=None):
		ctx = ClientContextFactory.getContext(self)
		if self.hostname and ClientTLSOptions is not None:  # workaround for TLS SNI
			ClientTLSOptions(self.hostname, ctx)
		return ctx


pluginPrintname = "[Foreca Ver. %s]" % VERSION
config.plugins.foreca.home = ConfigText(default="Germany/Berlin", fixed_size=False)
config.plugins.foreca.fav1 = ConfigText(default="United_States/New_York/New_York_City", fixed_size=False)
config.plugins.foreca.fav2 = ConfigText(default="Italy/Rome", fixed_size=False)
config.plugins.foreca.resize = ConfigSelection(default="0", choices=[("0", _("simple")), ("1", _("better"))])
config.plugins.foreca.bgcolor = ConfigSelection(default="#00000000", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.foreca.textcolor = ConfigSelection(default="#0038FF48", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.foreca.framesize = ConfigInteger(default=5, limits=(5, 99))
config.plugins.foreca.fontsize = ConfigInteger(default=20, limits=(20, 30))
config.plugins.foreca.slidetime = ConfigInteger(default=1, limits=(1, 60))
config.plugins.foreca.infoline = ConfigYesNo(default=True)
config.plugins.foreca.loop = ConfigYesNo(default=False)
config.plugins.foreca.citylabels = ConfigEnableDisable(default=True)
config.plugins.foreca.units = ConfigSelection(default="metrickmh", choices=[("metric", _("Metric (C, m/s)")), ("metrickmh", _("Metric (C, km/h)")), ("imperial", _("Imperial (C, mph)")), ("us", _("US (F, mph)"))])
config.plugins.foreca.time = ConfigSelection(default="24h", choices=[("12h", _("12 h")), ("24h", _("24 h"))])
config.plugins.foreca.debug = ConfigEnableDisable(default=True)


BASEURL = "https://www.foreca.com/"

HEADERS = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
}
HEADERS_API = {
	'User-Agent': HEADERS['User-Agent'],
	'Accept': 'application/json,text/plain,*/*',
	'Referer': BASEURL,
}


lng = 'en'
try:
	lng = config.osd.language.value
	lng = lng[:-3]
except:
	lng = 'en'
	pass


if not BASEURL.endswith("/"):
	BASEURL += "/"

MODULE_NAME = __name__.split(".")[-1]
MAIN_PAGE = BASEURL.rstrip("/")
USR_PATH = resolveFilename(SCOPE_CONFIG) + "Foreca"
PICON_PATH = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/picon/"
THUMB_PATH = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/thumb/"
print("BASEURL in uso:", BASEURL)

DEBUG = config.plugins.foreca.debug.value
AGENTS = [
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
	"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
	"Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
]


if DEBUG:
	print(pluginPrintname, "Debug enabled")
else:
	print(pluginPrintname, "Debug disabled")


# Make Path for Slideshow
CACHE_PATH = "/var/cache/Foreca/"
if not exists(CACHE_PATH):
	try:
		makedirs(CACHE_PATH, mode=0o755, exist_ok=True)
	except Exception:
		CACHE_PATH = "/tmp/"
		pass


def get_current_time():
	try:
		from datetime import datetime, timedelta, timezone
		return datetime.now(tz=timezone(timedelta(hours=-1)))
	except ImportError:
		class MyTimezone(datetime.tzinfo):
			def __init__(self, offset):
				self.offset = offset

			def utcoffset(self, dt):
				return self.offset

			def tzname(self, dt):
				return "Custom Timezone"

			def dst(self, dt):
				return timedelta(0)

		tz_offset = MyTimezone(timedelta(hours=-1))
		return datetime.now(tz=tz_offset)


def FAlog(info, wert=""):
	if config.plugins.foreca.debug.value:
		try:
			now = get_current_time()
			with open('/tmp/foreca.log', 'a') as f:
				f.write('{} {} {}'.format(now.strftime('%H:%M:%S'), info, wert))
		except IOError:
			print('[Foreca] Logging-Error')
	else:
		print('[Foreca] {} {}'.format(str(info), str(wert)))


# Make Path for user settings
if not exists(USR_PATH):
	try:
		makedirs(USR_PATH, mode=0o755, exist_ok=True)
	except Exception as e:
		print("Error creating directory: %s", e)


# Get screen size
size_w = getDesktop(0).size().width()
size_h = getDesktop(0).size().height()
HD = False if size_w < 1280 else True

# Get diacritics to handle
FILTERin = []
FILTERout = []
FILTERidx = 0

MAPPING = {"zh": "en"}
LANGUAGE = language.getActiveLanguage()[:2]  # "en_US" -> "en"
if LANGUAGE in MAPPING:
	LANGUAGE = MAPPING.get(LANGUAGE, "en")


try:
	setlocale(LC_COLLATE, language.getLanguage())
except Exception:
	FAlog("Collating sequence undeterminable; default used")

if exists(USR_PATH + "/Filter.cfg"):
	file = open(USR_PATH + "/Filter.cfg", "r")
	for line in file:
		regel = str(line)
		if regel[:2] == LANGUAGE and regel[4] == "Y":
			FILTERidx += 1
			FILTERin.append(regel[7:15].strip())
			FILTERout.append(regel[17:].strip())
	file.close


# ---------------------- Help Message Functions --------------------------------------------


def format_message(entries):
	max_left_width = max(len(entry[0]) for entry in entries)
	formatted_message = ""
	for entry in entries:
		left_column = entry[0]
		right_column = entry[1]
		spaces = " " * (max_left_width - len(left_column))
		formatted_message += "{:<{width}} =   {}\n".format(left_column + spaces, right_column, width=max_left_width)
	return formatted_message


# ---------------------- Skin Functions ----------------------------------------------------


def download_image(url, devicepath):
	try:
		req = Request(url, headers=HEADERS)
		resp = urlopen(req, timeout=10)
		with open(devicepath, 'wb') as f:
			f.write(resp.read())
		if DEBUG:
			FAlog("SatBild: Image saved to %s" % str(devicepath))
		return True
	except Exception as e:
		if DEBUG:
			FAlog("SatBild Error: Failed to download image", str(e))
		raise e


def getScale():
	return AVSwitch().getFramebufferScale()


def clean_url(url):
	return url.replace('\ufeff', '')


class MainMenuList(MenuList):

	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		GUIComponent.__init__(self)
		# default values:
		self.font0 = gFont("Regular", 28)
		self.font1 = gFont("Regular", 26)
		self.font2 = gFont("Regular", 28)
		self.font3 = gFont("Regular", 28)
		self.itemHeight = 120
		self.valTime = 5, 80, 100, 45
		self.valPict = 110, 45, 70, 70
		self.valPictScale = 0
		self.valTemp = 200, 55, 150, 40
		self.valTempUnits = 200, 95, 15, 40
		self.valWindPict = 320, 75, 35, 35
		self.valWindPictScale = 1
		self.valWind = 360, 55, 95, 40
		self.valWindUnits = 360, 95, 120, 40
		self.valText1 = 500, 0, 800, 42
		self.valText2 = 500, 45, 800, 42
		self.valText3 = 500, 90, 800, 42
		self.valText4 = 500, 135, 800, 42
		self.listCompleted = []
		self.callback = None
		self.idx = 0
		self.thumb = ""
		self.pos = 20
		if DEBUG:
			FAlog("MainMenuList...")

	def applySkin(self, desktop, parent):
		def warningWrongSkinParameter(string, wanted, given):
			print("[ForecaPreview] wrong '%s' skin parameters. Must be %d arguments (%d given)" % (string, wanted, given))

		def font0(value):
			self.font0 = parseFont(value, ((1, 1), (1, 1)))

		def font1(value):
			self.font1 = parseFont(value, ((1, 1), (1, 1)))

		def font2(value):
			self.font2 = parseFont(value, ((1, 1), (1, 1)))

		def font3(value):
			self.font3 = parseFont(value, ((1, 1), (1, 1)))

		def itemHeight(value):
			self.itemHeight = int(value)

		def setTime(value):
			self.valTime = list(map(int, value.split(",")))
			lx = len(self.valTime)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def setPict(value):
			self.valPict = list(map(int, value.split(",")))
			lx = len(self.valPict)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def setPictScale(value):
			self.valPictScale = int(value)

		def setTemp(value):
			self.valTemp = list(map(int, value.split(",")))
			lx = len(self.valTemp)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def setTempUnits(value):
			self.valTempUnits = list(map(int, value.split(",")))
			lx = len(self.valTempUnits)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def setWindPict(value):
			self.valWindPict = list(map(int, value.split(",")))
			lx = len(self.valWindPict)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def setWindPictScale(value):
			self.valWindPictScale = int(value)

		def setWind(value):
			self.valWind = list(map(int, value.split(",")))
			lx = len(self.valWind)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def setWindUnits(value):
			self.valWindUnits = list(map(int, value.split(",")))
			lx = len(self.valWindUnits)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def text1Pos(value):
			self.valText1 = list(map(int, value.split(",")))
			lx = len(self.valText1)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def text2Pos(value):
			self.valText2 = list(map(int, value.split(",")))
			lx = len(self.valText2)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def text3Pos(value):
			self.valText3 = list(map(int, value.split(",")))
			lx = len(self.valText3)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		def text4Pos(value):
			self.valText4 = list(map(int, value.split(",")))
			lx = len(self.valText4)
			if lx != 4:
				warningWrongSkinParameter(attrib, 4, lx)

		for (attrib, value) in list(self.skinAttributes):
			try:
				locals().get(attrib)(value)
				self.skinAttributes.remove((attrib, value))
			except Exception:
				pass
		self.l.setFont(0, self.font0)
		self.l.setFont(1, self.font1)
		self.l.setFont(2, self.font2)
		self.l.setFont(3, self.font3)
		self.l.setItemHeight(self.itemHeight)

		return GUIComponent.applySkin(self, desktop, parent)

	def buildEntries(self):
		if DEBUG:
			FAlog("buildEntries:", str(len(self.list)))
		if self.idx == len(self.list):
			self.setList(self.listCompleted)
			if self.callback:
				self.callback()
		else:
			self.downloadThumbnail()

	def downloadThumbnail(self):
		thumbUrl = self.list[self.idx][0]
		windDirection = self.list[self.idx][3]
		self.thumb = THUMB_PATH + str(thumbUrl + ".png")
		self.wind = THUMB_PATH + str(windDirection)
		self.buildEntry(None)

	def buildEntry(self, picInfo=None):
		self.x = self.list[self.idx]
		self.res = [(self.x[0], self.x[1])]

		""" Determine color base """
		# Color by temperature
		violetred = 0xC7D285
		mblau = 0x40b3ff
		weiss = 0xffffff

		# Manage temperature as a string
		temp_str = self.x[2]  # Es: "+18°"

		# Extract the number from the temperature string
		try:
			# Remove symbols and convert
			temp_clean = temp_str.replace('+', '').replace('°', '').replace('°C', '').replace('°F', '').strip()
			temp_value = int(float(temp_clean))  # Gestisci decimali
		except (ValueError, AttributeError):
			temp_value = 20  # Default if conversion fails

		if config.plugins.foreca.units.value == "us":
			self.centigrades = round((temp_value - 32) / 1.8)
			tempUnit = "°F"
		else:
			self.centigrades = temp_value  # Usa il valore numerico per i colori
			tempUnit = "°C"

		def getTempColor(temp):
			""" Determine color based on temperature """
			if temp <= -20:
				return 0x3b62ff
			elif temp <= -15:
				return 0x408cff
			elif temp <= -10:
				return 0x40b3ff
			elif temp <= -5:
				return 0x40d9ff
			elif temp <= 0:
				return 0x40ffff
			elif temp < 5:
				return 0x53c905
			elif temp < 10:
				return 0x77f424
			elif temp < 15:
				return 0xffff40
			elif temp < 20:
				return 0xffb340
			elif temp < 25:
				return 0xff6640
			elif temp < 30:
				return 0xff4040
			else:
				return 0xff40b3

		# Color management based on temperature
		self.tempcolor = getTempColor(self.centigrades)

		# Time
		x, y, w, h = self.valTime
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=0, text=self.x[1], color=weiss, color_sel=weiss))

		# forecast pictogram
		pngpic = LoadPixmap(self.thumb)
		if pngpic is not None:
			x, y, w, h = self.valPict
			self.res.append(MultiContentEntryPixmapAlphaTest(pos=(x, y), size=(w, h), png=pngpic))

		# Temp
		x, y, w, h = self.valTemp
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=0, text=_("Temp"), color=weiss, color_sel=weiss))
		x, y, w, h = self.valTempUnits
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=3, text=self.x[2], color=self.tempcolor, color_sel=self.tempcolor))  # Usa self.x[2] originale

		# wind pictogram
		pngpic = LoadPixmap(self.wind + ".png")
		if pngpic is not None:
			x, y, w, h = self.valWindPict
			self.res.append(MultiContentEntryPixmapAlphaTest(pos=(x, y), size=(w, h), png=pngpic))

		# Wind
		x, y, w, h = self.valWind
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=0, text=_("Wind"), color=weiss, color_sel=weiss))
		x, y, w, h = self.valWindUnits
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=3, text=self.x[4], color=violetred, color_sel=violetred))

		# Text
		x, y, w, h = self.valText1
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=3, text=_(self.x[5]), color=weiss, color_sel=weiss))

		x, y, w, h = self.valText2
		textsechs = self.x[6]
		textsechs = textsechs.replace("&deg;", "") + tempUnit
		textsechs = textsechs.replace("Feels Like:", _("Feels like:"))
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=2, text=textsechs, color=self.tempcolor, color_sel=self.tempcolor))

		x, y, w, h = self.valText3
		textsechs = self.x[7]
		textsechs = textsechs.replace("Precip chance:", _("Precip chance:"))
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=2, text=textsechs, color=mblau, color_sel=mblau))

		x, y, w, h = self.valText4
		textsechs = self.x[8]
		textsechs = textsechs.replace("Humidity:", _("Humidity:"))
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=2, text=textsechs, color=mblau, color_sel=mblau))

		self.listCompleted.append(self.res)
		self.idx += 1
		self.buildEntries()

	def SetList(self, lx):
		if DEBUG:
			FAlog("SetList")
		self.list = lx
		# self.l.setItemHeight(90)
		del self.listCompleted
		self.listCompleted = []
		self.idx = 0
		self.buildEntries()


class ForecaPreviewCache(Screen):

	if size_w == 1920:
		skin = """
		<screen position="center,center" size="80,80" backgroundColor="transparent" flags="wfNoBorder" zPosition="100" >
			<widget name="spinner" position="0,0" size="80,80"/>
		</screen>"""
	elif size_w == 2560:
		skin = """
		<screen position="center,center" size="80,80" backgroundColor="transparent" flags="wfNoBorder" zPosition="100">
			<widget name="spinner" position="0,0" size="80,80"/>
		</screen>"""
	else:
		skin = """
		<screen position="center,center" size="80,80" backgroundColor="transparent" flags="wfNoBorder" zPosition="100">
			<widget name="spinner" position="0,0" size="80,80"/>
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)

		self["spinner"] = Pixmap()
		self.curr = 0

		self.timer = eTimer()
		self.timer.callback.append(self.showNextSpinner)

	def start(self):
		self.show()
		self.timer.start(200, False)

	def stop(self):
		self.hide()
		self.timer.stop()

	def showNextSpinner(self):
		self.curr += 1
		if self.curr > 8:
			self.curr = 0
		png = LoadPixmap(cached=True, path=PICON_PATH + str(self.curr) + ".png")
		self["spinner"].instance.setPixmap(png)


class ForecaPreview(Screen, HelpableScreen):

	def __init__(self, session):
		global MAIN_PAGE
		self.session = session
		now = get_current_time()
		heute = now.strftime("%Y%m%d")
		if DEBUG:
			FAlog("determined local date:", str(heute))

		self.tag = 0

		# Get favorites
		global fav1, fav2, start
		fav1 = config.plugins.foreca.fav1.getValue()[config.plugins.foreca.fav1.getValue().rfind("/") + 1:]
		fav2 = config.plugins.foreca.fav2.getValue()[config.plugins.foreca.fav2.getValue().rfind("/") + 1:]
		start = config.plugins.foreca.home.getValue()[config.plugins.foreca.home.getValue().rfind("/") + 1:]

		# Get home location
		self.ort = config.plugins.foreca.home.value
		start = self.ort[self.ort.rfind("/") + 1:]
		MAIN_PAGE = "%s%s?lang=%s&details=%s&units=%s&tf=%s" % (
			BASEURL,
			pathname2url(self.ort),
			LANGUAGE,
			heute,
			config.plugins.foreca.units.value,
			config.plugins.foreca.time.value
		)
		if DEBUG:
			FAlog("initial link:", MAIN_PAGE)

		if size_w == 1920:
			self.skin = """
				<screen name="ForecaPreview" position="center,center" size="1200,900" title="Foreca Weather Forecast">
					<eLabel backgroundColor="red" position="10,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="green" position="305,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="yellow" position="600,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="blue" position="895,65" size="295,6" zPosition="11" />
					<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
					<eLabel backgroundColor="#999999" position="10,80" size="1180,1" />
					<widget backgroundColor="background" source="Titel" render="Label" position="13,775" size="1180,40" foregroundColor="yellow" font="Regular;32" halign="center" transparent="1" />
					<widget backgroundColor="background" source="Titel2" render="Label" position="13,123" size="1180,40" font="Regular;32" halign="center" transparent="1" />
					<widget backgroundColor="background" source="Titel3" render="Label" position="13,84" size="1180,40" foregroundColor="yellow" font="Regular;32" halign="center" transparent="1" />
					<widget backgroundColor="background" source="Titel4" render="Label" position="13,818" size="1180,40" font="Regular;32" halign="center" transparent="1" />
					<widget name="MainList" position="13,165" size="1180,600" zPosition="3" foregroundColor="#ffffff" backgroundColor="#000000" foregroundColorSelected="#ffffff" backgroundColorSelected="#999999" font0="Regular;30" font1="Regular;30" font2="Regular;28" font3="Regular;30" itemHeight="200" setTime="15,40,100,45" setPict="150,40,70,70" setPictScale="1" setTemp="280,50,200,40" setTempUnits="280,95,150,40" setWindPict="550,75,35,35" setWindPictScale="1" setWind="600,50,95,40" setWindUnits="600,95,50,40" text1Pos="720,0,600,42" text2Pos="720,50,600,42" text3Pos="720,100,600,42" text4Pos="720,150,600,42" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1" />
					<eLabel backgroundColor="#999999" position="10,770" size="1180,1" />
					<ePixmap position="1025,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png" />
					<ePixmap position="379,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png" />
					<ePixmap position="42,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" />
					<ePixmap position="705,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png" />
					<ePixmap position="1085,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_help.png" />
					<widget source="key_info" render="Label" position="771,864" size="250,35" font="Regular;30" />
					<!-- <widget source="key_menu" render="Label" position="441,864" size="250,35" font="Regular;30" /> -->
					<widget source="key_ok" render="Label" position="104,864" size="250,35" font="Regular;30" />
				</screen>"""
		elif size_w == 2560:
			self.skin = """
				<screen name="ForecaPreview" position="center,center" size="1600,1200" title="Foreca Weather Forecast">
					<eLabel backgroundColor="red" position="14,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="green" position="407,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="yellow" position="800,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="blue" position="1194,87" size="394,8" zPosition="11"/>
					<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#a08500" font="Regular;40" halign="center" position="800,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#18188b" font="Regular;40" halign="center" position="1194,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="#999999" position="14,107" size="1574,2"/>
					<widget backgroundColor="background" source="Titel" render="Label" position="18,1034" size="1574,54" foregroundColor="yellow" font="Regular;43" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel2" render="Label" position="18,164" size="1574,54" font="Regular;43" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel3" render="Label" position="18,112" size="1574,54" foregroundColor="yellow" font="Regular;43" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel4" render="Label" position="18,1091" size="1574,54" font="Regular;43" halign="center" transparent="1"/>
					<widget name="MainList" position="18,220" size="1574,800" zPosition="3" foregroundColor="#ffffff" backgroundColor="#000000" foregroundColorSelected="#ffffff" backgroundColorSelected="#999999" font0="Regular;30" font1="Regular;30" font2="Regular;28" font3="Regular;30" itemHeight="267" setTime="15,40,100,45" setPict="150,40,70,70" setPictScale="1" setTemp="280,50,200,40" setTempUnits="280,95,150,40" setWindPict="550,75,35,35" setWindPictScale="1" setWind="600,50,95,40" setWindUnits="600,95,50,40" text1Pos="720,0,600,42" text2Pos="720,50,600,42" text3Pos="720,100,600,42" text4Pos="720,150,600,42" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1"/>
					<eLabel backgroundColor="#999999" position="14,1027" size="1574,2"/>
					<ePixmap position="1367,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
					<ePixmap position="506,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
					<ePixmap position="56,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="940,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
					<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="1447,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
					<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_help.png"/>
					<widget source="key_info" render="Label" position="1028,1152" size="334,47" font="Regular;40"/>
					<!-- <widget source="key_menu" render="Label" position="588,1152" size="334,47" font="Regular;40"/> -->
					<widget source="key_ok" render="Label" position="139,1152" size="334,47" font="Regular;40"/>
				</screen>"""
		else:
			self.skin = """
				<screen name="ForecaPreview" position="center,center" size="800,600" title="Foreca Weather Forecast">
					<eLabel backgroundColor="red" position="6,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="green" position="203,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="yellow" position="400,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="blue" position="596,43" size="196,4" zPosition="11"/>
					<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#a08500" font="Regular;20" halign="center" position="400,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#18188b" font="Regular;20" halign="center" position="596,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="#999999" position="6,53" size="786,1"/>
					<widget backgroundColor="background" source="Titel" render="Label" position="8,516" size="786,26" foregroundColor="yellow" font="Regular;21" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel2" render="Label" position="8,82" size="786,26" font="Regular;21" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel3" render="Label" position="8,56" size="786,26" foregroundColor="yellow" font="Regular;21" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel4" render="Label" position="8,545" size="786,26" font="Regular;21" halign="center" transparent="1"/>
					<widget name="MainList" position="8,110" size="786,400" zPosition="3" foregroundColor="#ffffff" backgroundColor="#000000" foregroundColorSelected="#ffffff" backgroundColorSelected="#999999" font0="Regular;30" font1="Regular;30" font2="Regular;28" font3="Regular;30" itemHeight="133" setTime="15,40,100,45" setPict="150,40,70,70" setPictScale="1" setTemp="280,50,200,40" setTempUnits="280,95,150,40" setWindPict="550,75,35,35" setWindPictScale="1" setWind="600,50,95,40" setWindUnits="600,95,50,40" text1Pos="720,0,600,42" text2Pos="720,50,600,42" text3Pos="720,100,600,42" text4Pos="720,150,600,42" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1"/>
					<eLabel backgroundColor="#999999" position="6,513" size="786,1"/>
					<ePixmap position="683,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
					<ePixmap position="252,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
					<ePixmap position="28,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="470,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
					<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="723,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
					<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_help.png"/>
					<widget source="key_info" render="Label" position="514,576" size="166,23" font="Regular;20"/>
					<!-- <widget source="key_menu" render="Label" position="294,576" size="166,23" font="Regular;20"/> -->
					<widget source="key_ok" render="Label" position="69,576" size="166,23" font="Regular;20"/>
				</screen>"""

		Screen.__init__(self, session)
		self.setTitle(_("Foreca Weather Forecast") + " " + _("v.") + VERSION)
		self["MainList"] = MainMenuList()
		self["Titel"] = StaticText()
		self["Titel2"] = StaticText(_("Please wait ..."))
		self["Titel3"] = StaticText()
		self["Titel4"] = StaticText()
		self["Titel5"] = StaticText()
		self["key_red"] = StaticText(_("Week"))
		self["key_ok"] = StaticText(_("Config"))

		self["key_green"] = StaticText('')
		self["key_yellow"] = StaticText('')
		self["key_blue"] = StaticText('')

		self["key_info"] = StaticText(_("Legend"))
		# self["key_menu"] = StaticText(_("Maps"))
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"cancel": (self.exit, _("Exit - End")),
				# "menu": (self.Menu, _("Menu - Weather maps")),
				"showEventInfo": (self.info, _("Info - Legend")),
				"ok": (self.PicSetupMenu, _("OK - Config")),
				"left": (self.left, _("Left - Previous day")),
				"right": (self.right, _("Right - Next day")),
				"up": (self.up, _("Up - Previous page")),
				"down": (self.down, _("Down - Next page")),
				"previous": (self.previousDay, _("Left arrow - Previous day")),
				"next": (self.nextDay, _("Right arrow - Next day")),
				"red": (self.red, _("Red - Weekoverview")),
				"green": (self.Fav1, _("Green - Favorite 1")),
				"yellow": (self.Fav2, _("Yellow - Favorite 2")),
				"blue": (self.Fav0, _("Blue - Home")),
				"tv": (self.OK, _("Tv - City")),
				"text": (self.OK, _("text - City")),
				"0": (boundFunction(self.keyNumberGlobal, 0), _("0 - Today")),
				"1": (boundFunction(self.keyNumberGlobal, 1), _("1 - Today + 1 day")),
				"2": (boundFunction(self.keyNumberGlobal, 2), _("2 - Today + 2 days")),
				"3": (boundFunction(self.keyNumberGlobal, 3), _("3 - Today + 3 days")),
				"4": (boundFunction(self.keyNumberGlobal, 4), _("4 - Today + 4 days")),
				"5": (boundFunction(self.keyNumberGlobal, 5), _("5 - Today + 5 days")),
				"6": (boundFunction(self.keyNumberGlobal, 6), _("6 - Today + 6 days")),
				"7": (boundFunction(self.keyNumberGlobal, 7), _("7 - Today + 7 days")),
				"8": (boundFunction(self.keyNumberGlobal, 8), _("8 - Today + 8 days")),
				"9": (boundFunction(self.keyNumberGlobal, 9), _("9 - Today + 9 days")),
			},
			-2
		)
		self.onLayoutFinish.append(self.StartPageFirst)
		self.onShow.append(self.update_button)

	def update_button(self):
		if config.plugins.foreca.citylabels.value:
			self["key_green"].setText(fav1.replace("_", " "))
			self["key_yellow"].setText(fav2.replace("_", " "))
			self["key_blue"].setText(start.replace("_", " "))
		else:
			self["key_green"].setText(_("Favorite 1"))
			self["key_yellow"].setText(_("Favorite 2"))
			self["key_blue"].setText(_("Home"))

		self["key_red"].setText(_("Maps"))
		self["Titel4"].text = self.ort[self.ort.rfind("/") + 1:].replace("_", " ")

	def PicSetupMenu(self):
		self.session.openWithCallback(self.OKCallback, PicSetup)

	def StartPageFirst(self):
		print("[Foreca] === STARTPAGEFIRST CALLED ===")
		if DEBUG:
			FAlog("StartPageFirst...")
		self.cacheDialog = self.session.instantiateDialog(ForecaPreviewCache)
		self["MainList"].callback = self.deactivateCacheDialog
		self.working = False
		self["MainList"].show()
		self.cacheDialog.start()

		callInThread(self.getPage)

	def onLayoutFinished(self):
		print("[Foreca] === ONLAYOUTFINISHED CALLED ===")
		callInThread(self.getPage)

	def StartPage(self):
		print("[Foreca] === GETPAGE CALLED ===")
		self["Titel"].text = ""
		self["Titel3"].text = ""
		self["Titel4"].text = ""
		self["Titel5"].text = ""
		self["Titel2"].text = _("Please wait ...")
		self.working = False
		if DEBUG:
			FAlog("MainList show...")
		self["MainList"].show
		callInThread(self.getPage)

	def getPage(self, page=None):
		print("[Foreca] getPage:", page)
		if DEBUG:
			FAlog("getPage...")

		self.cacheDialog.start()
		self.working = True
		if not page:
			page = ""
		url = MAIN_PAGE + str(page)

		if DEBUG:
			FAlog("page link: " + str(url))
		print("[Foreca] getPage: " + str(url))
		try:
			req = Request(url, headers=HEADERS)
			if DEBUG:
				FAlog("Request headers: " + str(HEADERS))

			resp = urlopen(req, timeout=10)
			html_content = resp.read().decode('utf-8') if PY3 else resp.read()

			if DEBUG:
				FAlog("HTTP Status Code: " + str(resp.getcode()))
				FAlog("Response length: " + str(len(html_content)))
				FAlog("First 500 chars of response: " + str(html_content[:500]))
				with open('/tmp/foreca_response.html', 'w') as f:
					f.write(html_content)

			# THIS IS AN IMPORTANT CALL!
			self.getForecaPage(html_content)

			FAlog("Searching for API patterns...")

		except Exception as e:
			FAlog("Error in getPage: " + str(e))
			self.error(repr(e))

		self.update_button()
		self.deactivateCacheDialog()

	def getForecaPage(self, html):
		"""Simplified version that uses only JSON parsing"""
		print("[Foreca] === FORECA PARSING START ===")

		try:
			# Initialize location
			foundPos = self.ort.find("/")
			if foundPos != -1:
				plaats = _(self.ort[0:foundPos]) + ", " + self.ort[foundPos + 1:len(self.ort)]
				self.plaats = plaats.replace("_", " ")
			else:
				self.plaats = self.ort.replace("_", " ")

			print(f"[Foreca] Location: {self.plaats}")
			print(f"[Foreca] Current tag: {self.tag}")

			# FIRST TRY: Modern JSON parsing
			print("[Foreca] Attempting JSON parsing...")
			datalist = self.extractModernHourlyData(html)

			if datalist:
				print(f"[Foreca] SUCCESS: Got {len(datalist)} data points from JSON parsing!")
				parsed_data = self.parseJSONWeatherData(datalist)
				self.displayWeatherData(parsed_data, "JSON Forecast")
			else:
				print("[Foreca] FAILED: No data from JSON parsing")
				self.displayWeatherData([], "No Data Available")

		except Exception as e:
			print(f"[Foreca] ERROR in getForecaPage: {e}")
			import traceback
			traceback.print_exc()
			self.displayWeatherData([], "Error")

	def error(self, err=""):
		if DEBUG:
			FAlog("getPage Error:", err)
		self.working = False
		self.deactivateCacheDialog()

	def deactivateCacheDialog(self):
		print(pluginPrintname, "deactivateCacheDialog")
		self.cacheDialog.stop()
		self.working = False

	def exit(self):
		try:
			unlink(CACHE_PATH + "sat.jpg")
		except Exception:
			pass

		try:
			unlink(CACHE_PATH + "sat.html")
		except Exception:
			pass

		try:
			unlink(CACHE_PATH + "meteogram.png")
		except Exception:
			pass
		self.deactivateCacheDialog()
		self.close()

	def keyNumberGlobal(self, number):
		self.tag = number
		self.Zukunft(self.tag)
		FAlog("Jump to day: " + str(self.tag))

	def titel(self):
		print("[Foreca] titel called with tag:", self.tag)

		# Determine day text
		if self.tag == 0:
			day_text = _("Today")
		elif self.tag == 1:
			day_text = _("Tomorrow")
		else:
			day_text = _("Day") + " +" + str(self.tag)

		# Get date string
		current_date = get_current_time()
		display_date = current_date + timedelta(days=self.tag)
		date_str = display_date.strftime('%d/%m/%Y')

		title = _("Foreca Weather Forecast") + " " + _("v.") + VERSION + f" - {day_text} ({date_str})"
		self.setTitle(title)
		print("[Foreca] Setting title:", title)

	def Fav0(self):
		global start
		self.ort = config.plugins.foreca.home.value
		start = self.ort[self.ort.rfind("/") + 1:]
		print(pluginPrintname, "Fav0 ort location:", self.ort)
		self.tag = 0
		self.titel()
		self.Zukunft(0)

	def Fav1(self):
		global fav1
		self.ort = config.plugins.foreca.fav1.value
		fav1 = self.ort[self.ort.rfind("/") + 1:]
		print(pluginPrintname, "Fav1 ort location:", self.ort)
		self.tag = 0
		self.titel()
		self.Zukunft(0)

	def Fav2(self):
		global fav2
		self.ort = config.plugins.foreca.fav2.value
		fav2 = self.ort[self.ort.rfind("/") + 1:]
		print(pluginPrintname, "Fav2 ort location:", self.ort)
		self.tag = 0
		self.titel()
		self.Zukunft(0)

	def Zukunft(self, ztag=0):
		global MAIN_PAGE
		print("[Foreca] Zukunft called with offset:", ztag)
		print("[Foreca] Current location:", self.ort)

		self.tag = ztag  # Store the day offset

		# Build URL with correct day parameter
		if ztag == 0:
			# Today - use main page
			MAIN_PAGE = "%s%s?lang=%s&units=%s&tf=%s" % (
				BASEURL,
				pathname2url(self.ort),
				LANGUAGE,
				config.plugins.foreca.units.value,
				config.plugins.foreca.time.value
			)
		else:
			# Future days - use hourly endpoint with day parameter
			MAIN_PAGE = "%s%s/hourly?lang=%s&day=%s&units=%s&tf=%s" % (
				BASEURL,
				pathname2url(self.ort),
				LANGUAGE,
				ztag,  # This should be 1 for tomorrow, 2 for day after, etc.
				config.plugins.foreca.units.value,
				config.plugins.foreca.time.value
			)

		if DEBUG:
			print("[Foreca] Day link: " + MAIN_PAGE + ", day offset: " + str(ztag))

		print("[Foreca] New MAIN_PAGE:", MAIN_PAGE)
		self.StartPage()

	def info(self):
		message = str("%s" % (_("Server URL:    %s\n") % BASEURL))
		entries = [
			(_("VERSION"), VERSION),
			(_("Wind direction"), _("Arrow to right: Wind from the West")),
			(_("Ok"), _("Go to Config Plugin")),
			(_("Red"), _("Weather maps and forecasts")),
			(_("Green"), _("Go to Favorite 1")),
			(_("Yellow"), _("Go to Favorite 2")),
			(_("Blue"), _("Go to Home")),
			(_("Tv/Txt"), _("Go to City Panel")),
			# (_("Menu"), _("Satellite photos and maps")),
			(_("Up/Down"), _("Previous/Next page")),
			(_("<   >"), _("Prognosis Previous/Next day")),
			(_("0 - 9"), _("Prognosis (x) days from now"))
		]
		message += format_message(entries)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

	def OK(self):
		self.city = self.ort
		print("[Foreca] OK:", self.city)
		self.session.openWithCallback(self.OKCallback, CityPanel, self.city)

	def OKCallback(self, callback=None):
		global fav1, fav2
		print('OKCallback callback=,', str(callback))
		fav1 = config.plugins.foreca.fav1.getValue()[config.plugins.foreca.fav1.getValue().rfind("/") + 1:]
		fav2 = config.plugins.foreca.fav2.getValue()[config.plugins.foreca.fav2.getValue().rfind("/") + 1:]

		self.ort = config.plugins.foreca.home.getValue()
		if callback is not None:
			self.ort = callback
		self.tag = 0
		self.Zukunft(self.tag)

		if DEBUG:
			FAlog("MenuCallback")

		self.update_button()

		self.deactivateCacheDialog()

	def left(self):
		if not self.working and self.tag > 0:  # Allow only until today (tag 0)
			self.tag = self.tag - 1
			self.Zukunft(self.tag)
			FAlog("Previous day: " + str(self.tag))

	def right(self):
		if not self.working and self.tag < 9:  # Maximum 9 days in the future
			self.tag = self.tag + 1
			self.Zukunft(self.tag)
			FAlog("Next day: " + str(self.tag))

	def up(self):
		if not self.working:
			self["MainList"].pageUp()

	def down(self):
		if not self.working:
			self["MainList"].pageDown()

	def previousDay(self):
		self.left()

	def nextDay(self):
		self.right()

	def red(self):
		"""Show weather maps selection instead of meteogram"""
		try:
			# Lista delle mappe meteo disponibili
			weather_maps = [
				(_("Temperature Map"), "temp_map.png", _("Temperature forecast")),
				(_("Pressure Map"), "pressure_map.png", _("Air pressure forecast")),
				(_("Cloud Cover Map"), "cloud_map.png", _("Cloud cover and precipitation")),
				(_("Satellite Map"), "sat_map.png", _("Satellite weather view")),
				(_("Rain Radar Map"), "rain_map.png", _("Precipitation radar")),
			]

			# Filtra solo le mappe che esistono
			available_maps = []
			for name, map_file, desc in weather_maps:
				map_path = THUMB_PATH + map_file
				if exists(map_path):
					available_maps.append((name, map_file, desc))

			if not available_maps:
				self.session.open(MessageBox, _("No weather maps available"), MessageBox.TYPE_INFO)
				return

			choice_list = []
			for name, map_file, desc in available_maps:
				choice_list.append((f"{name} - {desc}", map_file))

			self.session.openWithCallback(
				self.weatherMapSelected,
				ChoiceBox,
				title=_("Select Weather Map"),
				list=choice_list
			)

		except Exception as e:
			print("[Foreca] Error in red button: %s" % str(e))
			self.session.open(MessageBox, _("Error loading weather maps"), MessageBox.TYPE_ERROR)

	def Menu(self):
		# self.session.openWithCallback(self.MenuCallback, SatPanel, self.ort)
		pass

	def MenuCallback(self):
		global start, fav1, fav2
		fav1 = config.plugins.foreca.fav1.getValue()[config.plugins.foreca.fav1.getValue().rfind("/") + 1:]
		fav2 = config.plugins.foreca.fav2.getValue()[config.plugins.foreca.fav2.getValue().rfind("/") + 1:]
		start = config.plugins.foreca.home.getValue()[config.plugins.foreca.home.getValue().rfind("/") + 1:]

		self.city = config.plugins.foreca.home.getValue()
		self.ort = config.plugins.foreca.home.getValue()  # self.city
		self.update_button()

	def displayWeatherData(self, datalist, source):
		"""Display data with proper day information"""
		print("[Foreca] displayWeatherData called with %d items from %s" % (len(datalist), source))

		# Determine day text and date
		if self.tag == 0:
			day_text = _("Today")
		elif self.tag == 1:
			day_text = _("Tomorrow")
		else:
			day_text = _("Day") + " +" + str(self.tag)

		current_date = get_current_time()
		display_date = current_date + timedelta(days=self.tag)
		date_str = display_date.strftime('%d/%m/%Y')

		if not datalist:
			self["Titel2"].text = _("No weather data available")
			self["Titel3"].text = f"Foreca - {day_text} {date_str}"
			self["Titel4"].text = self.plaats
			self["Titel5"].text = ""
			self.titel()
			self["MainList"].SetList([])
		else:
			self["Titel2"].text = ""
			self["Titel3"].text = f"Foreca - {day_text} {date_str}"
			self["Titel4"].text = self.plaats
			self["Titel5"].text = f"{len(datalist)}h forecast"
			self.titel()
			print("[Foreca] Setting list with %d items for %s" % (len(datalist), day_text))
			self["MainList"].SetList(datalist)

		print("[Foreca] DISPLAYED %d ITEMS" % len(datalist))

	def extractModernHourlyData(self, html_content, debug=False):
		print("[Foreca] === extractModernHourlyData START ===")
		print("[Foreca] HTML length: " + str(len(html_content)))

		# Save HTML for analysis
		try:
			with open('/tmp/foreca_debug.html', 'w') as f:
				f.write(html_content)
			print("[Foreca] HTML saved to /tmp/foreca_debug.html")
		except:
			pass

		json_patterns = [
			r'data:\s*(\[.*?\]),\s*data3h:',
			r'data:\s*(\[.*?\])',
			r'window\.__DATA__\s*=\s*({.*?});',
			r'var\s+forecaData\s*=\s*({.*?});',
			r'"hourly":\s*(\[.*?\])',
			r'"hours":\s*(\[.*?\])',
			r'"temperature":\s*(\[.*?\])',
		]

		for i, pattern in enumerate(json_patterns):
			try:
				print(f"[Foreca] Trying pattern {i}: {pattern[:50]}...")
				matches = findall(pattern, html_content, DOTALL)
				print(f"[Foreca] Pattern {i}: Found {len(matches)} matches")

				if matches:
					match_content = matches[0]
					print(f"[Foreca] Pattern {i} SUCCESS, length: {len(match_content)}")
					print(f"[Foreca] First 300 chars: {match_content[:300]}...")

					# Save the matched JSON for analysis
					try:
						with open(f'/tmp/foreca_pattern_{i}.json', 'w') as f:
							f.write(match_content)
						print(f"[Foreca] Pattern {i} data saved to /tmp/foreca_pattern_{i}.json")
					except:
						pass

					# Try to parse the JSON
					try:
						data = loads(match_content)
						print(f"[Foreca] JSON parsed successfully: type={type(data)}, length={len(data) if isinstance(data, list) else 'N/A'}")
						if isinstance(data, list) and data:
							print(f"[Foreca] First item keys: {list(data[0].keys())}")
							print(f"[Foreca] Sample data: {data[0]}")
						return data
					except Exception as e:
						print(f"[Foreca] JSON parse error: {e}")
						continue

			except Exception as e:
				print(f"[Foreca] Pattern {i} search error: {e}")
				continue

		print("[Foreca] === extractModernHourlyData FAILED - No patterns matched ===")
		return None

	def parseJSONWeatherData(self, weather_data):
		"""Parse Foreca JSON data - PROPER TIME SORTING"""
		try:
			print("[Foreca] === DEBUG WEATHER DATA ===")
			print("[Foreca] Total data points: %d" % len(weather_data))
			if weather_data:
				print("[Foreca] First 3 items:")
				for i in range(min(3, len(weather_data))):
					print("[Foreca]   %d: %s" % (i, weather_data[i]))
			print("[Foreca] Requested day offset: %d" % self.tag)

			datalist = []
			print("[Foreca] Parsing weather data for day offset=%d" % self.tag)

			translation_dict = self.load_translation_dict(LANGUAGE)

			# ⚠️ FIX: When day=1 in URL, we already get tomorrow's data
			# Don't apply additional offset in parsing!
			if self.tag == 0:
				# Today - take first 24 hours
				start_index = 0
				end_index = min(24, len(weather_data))
			else:
				# Future days - the API already returns the correct day
				# Just take available hours (usually 24)
				start_index = 0
				end_index = len(weather_data)

			filtered_data = weather_data[start_index:end_index]
			print("[Foreca] Taking hours %d to %d for day %d" % (start_index, end_index, self.tag))

			# Sort data chronologically
			try:
				from datetime import datetime

				def get_sort_key(hour_data):
					time_str = hour_data.get('time', '')
					try:
						return datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
					except:
						return time_str

				filtered_data_sorted = sorted(filtered_data, key=get_sort_key)
				print("[Foreca] Data sorted chronologically")

			except Exception as e:
				print("[Foreca] Datetime sorting failed: %s" % e)
				filtered_data_sorted = filtered_data

			# Parse each hour
			for hour_data in filtered_data_sorted:
				try:
					# Extract time
					time_str = hour_data.get('time', '')
					if 'T' in time_str:
						time_str = time_str.split('T')[1][:5]

					# Temperature
					temp_value = hour_data.get('temp', 20)
					temp_str = "+%d°" % temp_value if temp_value > 0 else "%d°" % temp_value

					# Weather condition
					wx_condition = hour_data.get('wx', '')
					symb = hour_data.get('symb', 'd000')

					if wx_condition:
						condition = wx_condition
					else:
						condition = self.symbolToCondition(symb)

					condition = self.translate_description(condition, translation_dict)

					# Wind
					wind_speed_kmh = hour_data.get('windskmh', hour_data.get('winds', 10))
					wind_speed = "%d km/h" % wind_speed_kmh

					wind_cardinal = hour_data.get('windCardinal', '')
					if wind_cardinal:
						wind_dir = "w" + wind_cardinal
					else:
						wind_dir_deg = hour_data.get('windd', 0)
						wind_dir = self.degreesToWindDirection(wind_dir_deg)

					# Additional data
					feels_temp = hour_data.get('flike', temp_value)
					feels_str = _("Feels like:") + " +%d°" % feels_temp if feels_temp > 0 else _("Feels like:") + " %d°" % feels_temp

					precip_chance = hour_data.get('rainp', 0)
					precip_str = _("Precipitations:") + " %d%%" % precip_chance

					humidity = hour_data.get('rhum', 50)
					humidity_str = _("Humidity:") + " %d%%" % humidity

					# Create row
					row = [
						symb, time_str, temp_str, wind_dir, wind_speed,
						condition, feels_str, precip_str, humidity_str
					]

					datalist.append(row)
					print("[Foreca] Added hour: %s - %s" % (time_str, temp_str))

				except Exception as e:
					print("[Foreca] Error parsing hour data: %s" % str(e))
					continue

			print("[Foreca] Successfully parsed %d hours for day %d" % (len(datalist), self.tag))
			return datalist

		except Exception as e:
			print("[Foreca] Error in parseJSONWeatherData: %s" % str(e))
			import traceback
			traceback.print_exc()
			return []

	def symbolToCondition(self, symbol):
		"""Convert Foreca symbol to text condition - SAFE MAPPING"""
		symbol_map = {
			# Clear
			'd000': 'Clear', 'n000': 'Clear', 'd001': 'Clear', 'n001': 'Clear',

			# Mostly clear
			'd100': 'Mostly clear', 'n100': 'Mostly clear', 'd101': 'Mostly clear', 'n101': 'Mostly clear',

			# Partly cloudy
			'd200': 'Partly cloudy', 'n200': 'Partly cloudy', 'd201': 'Partly cloudy', 'n201': 'Partly cloudy',
			'd202': 'Partly cloudy', 'n202': 'Partly cloudy',

			# Cloudy
			'd300': 'Cloudy', 'n300': 'Cloudy', 'd301': 'Cloudy', 'n301': 'Cloudy',

			# Overcast
			'd400': 'Overcast', 'n400': 'Overcast', 'd401': 'Overcast', 'n401': 'Overcast',

			# Fog
			'd500': 'Fog', 'n500': 'Fog', 'd501': 'Fog', 'n501': 'Fog',

			# Light rain
			'd210': 'Light rain', 'n210': 'Light rain', 'd211': 'Light rain', 'n211': 'Light rain',
			'd212': 'Light rain', 'n212': 'Light rain', 'd310': 'Light rain', 'n310': 'Light rain',
			'd311': 'Light rain', 'n311': 'Light rain', 'd312': 'Light rain', 'n312': 'Light rain',
			'd410': 'Light rain', 'n410': 'Light rain',

			# Rain
			'd220': 'Rain', 'n220': 'Rain', 'd222': 'Rain', 'n222': 'Rain',
			'd320': 'Rain', 'n320': 'Rain', 'd322': 'Rain', 'n322': 'Rain',
			'd420': 'Rain', 'n420': 'Rain',

			# Heavy rain
			'd230': 'Heavy rain', 'n230': 'Heavy rain', 'd231': 'Heavy rain', 'n231': 'Heavy rain',
			'd232': 'Heavy rain', 'n232': 'Heavy rain', 'd240': 'Heavy rain', 'n240': 'Heavy rain',
			'd330': 'Heavy rain', 'n330': 'Heavy rain', 'd331': 'Heavy rain', 'n331': 'Heavy rain',
			'd332': 'Heavy rain', 'n332': 'Heavy rain', 'd340': 'Heavy rain', 'n340': 'Heavy rain',
			'd430': 'Heavy rain', 'n430': 'Heavy rain',

			# Thunderstorm
			'd221': 'Thunderstorm', 'n221': 'Thunderstorm', 'd321': 'Thunderstorm', 'n321': 'Thunderstorm',
			'd421': 'Thunderstorm', 'n421': 'Thunderstorm',

			# Snow
			'd600': 'Snow', 'n600': 'Snow', 'd610': 'Snow', 'n610': 'Snow',
			'd620': 'Snow', 'n620': 'Snow', 'd630': 'Snow', 'n630': 'Snow',

			# Sleet
			'd700': 'Sleet', 'n700': 'Sleet', 'd710': 'Sleet', 'n710': 'Sleet',
			'd720': 'Sleet', 'n720': 'Sleet', 'd730': 'Sleet', 'n730': 'Sleet',
		}

		condition = symbol_map.get(symbol, 'Unknown')
		print(f"[Foreca] Symbol mapping: {symbol} -> {condition}")
		return condition

	def degreesToWindDirection(self, degrees):
		"""Convert degrees to available wind direction icons"""
		# Map to available icons: w000(N), w045(NE), w090(E), w135(SE), w180(S), w225(SW), w270(W), w315(NW)
		if 337.5 <= degrees or degrees < 22.5:
			return 'w000'  # N
		elif 22.5 <= degrees < 67.5:
			return 'w045'  # NE
		elif 67.5 <= degrees < 112.5:
			return 'w090'  # E
		elif 112.5 <= degrees < 157.5:
			return 'w135'  # SE
		elif 157.5 <= degrees < 202.5:
			return 'w180'  # S
		elif 202.5 <= degrees < 247.5:
			return 'w225'  # SW
		elif 247.5 <= degrees < 292.5:
			return 'w270'  # W
		elif 292.5 <= degrees < 337.5:
			return 'w315'  # NW
		else:
			return 'w000'  # Default

	def load_translation_dict(self, lng):
		print("[Foreca] load_translation_dict:", lng)
		dict_file = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/dict/%sdict.txt" % lng
		if not exists(dict_file):
			dict_file = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/dict/endict.txt"
		translation_dict = {}
		with open(dict_file, 'r') as file:
			for line in file:
				parts = line.strip().split('=')
				if len(parts) == 2:
					key, value = parts
					translation_dict[key.strip().lower()] = value.strip()
		return translation_dict

	def translate_description(self, description, translation_dict):
		# Clean the description from tabs, carriage returns, and newlines
		cleaned_description = sub(r"[\t\r\n]", " ", description).strip()
		# Separate punctuation to avoid incorrect translations
		words = sub(r"([.,!?])", r" \1 ", cleaned_description).split()
		translated_words = []
		for word in words:
			is_capitalized = word[0].isupper() if word else False
			translated_word = translation_dict.get(word.lower(), word)
			# Restore capitalization if needed
			if is_capitalized:
				translated_word = translated_word.capitalize()
			translated_words.append(translated_word)
		return " ".join(translated_words).replace(" .", ".").replace(" ,", ",").replace(" !", "!").replace(" ?", "?")

	def filter_dia(self, text):
		filterItem = 0
		while filterItem < FILTERidx:
			text = text.replace(FILTERin[filterItem], FILTERout[filterItem])
			filterItem += 1
		return text

	def konvert_uml(self, text):
		text = self.filter_dia(text)
		return text[text.rfind("\\t") + 2:len(text)]

	def loadPicture(self, url=""):
		"""Load meteogram - either extract data or use alternative"""
		print("[Foreca] === LOAD PICTURE START ===")

		try:
			devicepath = CACHE_PATH + "meteogram.png"

			# Clear previous
			if exists(devicepath):
				remove(devicepath)

			print("[Foreca] Downloading meteogram page from: %s" % url)

			# Download HTML page
			headers = {
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
			}

			req = Request(url, headers=headers)
			resp = urlopen(req, timeout=20)
			html_content = resp.read().decode('utf-8')
			print("[Foreca] Downloaded HTML, length: %d bytes" % len(html_content))

			# Try to extract meteogram data
			meteogram_data = self.extractMeteogramData(html_content)

			if meteogram_data:
				print("[Foreca] Meteogram data extracted, creating summary...")
				# Create a simple text-based meteogram summary
				self.createMeteogramSummary(meteogram_data, devicepath)
			else:
				# Fallback: Use local weather map
				print("[Foreca] No meteogram data, using fallback")
				self.useMeteogramFallback(devicepath)

			# Show the result
			from twisted.internet import reactor
			reactor.callFromThread(self.showMeteogram, devicepath)

		except Exception as e:
			print("[Foreca] Error in loadPicture: %s" % e)
			from twisted.internet import reactor
			reactor.callFromThread(self.showError, _("Failed to load meteogram: %s") % str(e))

	def extractMeteogramData(self, html_content):
		"""Extract meteogram data from the HTML page"""
		print("[Foreca] === EXTRACT METEOGRAM DATA ===")

		try:
			# Pattern per trovare i dati del meteogramma
			patterns = [
				r'window\.renderMeteogram\(\s*\{[^}]*data:\s*(\[[^\]]*\])',
				r'renderMeteogram\(\s*\{[^}]*data:\s*(\[[^\]]*\])',
				r'data:\s*(\[.*?\])\s*,\s*[}]\)'
			]

			for i, pattern in enumerate(patterns):
				matches = findall(pattern, html_content, DOTALL)
				if matches:
					print("[Foreca] Found meteogram data with pattern %d" % i)
					json_data = matches[0]
					print("[Foreca] Meteogram data length: %d" % len(json_data))
					print("[Foreca] Sample data: %s..." % json_data[:200])

					try:
						data = loads(json_data)
						print("[Foreca] Meteogram JSON parsed successfully: %d points" % len(data))
						return data
					except Exception as e:
						print("[Foreca] Error parsing meteogram JSON: %s" % e)
						continue

			print("[Foreca] No meteogram data found in HTML")
			return None

		except Exception as e:
			print("[Foreca] Error extracting meteogram data: %s" % e)
			return None

	def createMeteogramSummary(self, data, output_path):
		"""Create a simple text-based meteogram summary"""
		try:
			print("[Foreca] Creating meteogram summary from %d data points" % len(data))

			# Extract key information
			summary_lines = []
			summary_lines.append("=== FORECA 5-DAY FORECAST ===")
			summary_lines.append("Time    Temp Precip Condition")
			summary_lines.append("-" * 40)

			for hour_data in data[:24]:  # Show first 24 hours
				time_str = hour_data.get('time', '')[-8:-3]  # Extract HH:MM
				temp = hour_data.get('temp', 0)
				precip = hour_data.get('rain', 0)
				condition = hour_data.get('wx', 'Unknown')

				summary_lines.append(f"{time_str}   {temp:2}°C   {precip:3}mm   {condition}")

			summary_text = "\n".join(summary_lines)

			# Save as text file (or could create a simple image)
			with open(output_path.replace('.png', '.txt'), 'w') as f:
				f.write(summary_text)

			print("[Foreca] Meteogram summary created")

			# For now, use a local image since we can't easily create PNG
			self.useMeteogramFallback(output_path)

		except Exception as e:
			print("[Foreca] Error creating meteogram summary: %s" % e)
			self.useMeteogramFallback(output_path)

	def useMeteogramFallback(self, output_path):
		"""Use a local weather map as fallback"""
		try:
			# Copy a local weather map image
			local_images = [
				THUMB_PATH + "temp_map.png",
				THUMB_PATH + "pressure_map.png",
				THUMB_PATH + "cloud_map.png",
				THUMB_PATH + "sat_map.png"
			]

			for local_img in local_images:
				if exists(local_img):
					import shutil
					shutil.copy2(local_img, output_path)
					print("[Foreca] Using fallback image: %s" % local_img)
					return

			# Create a simple colored image as last resort
			self.createSimpleMeteogramImage(output_path)

		except Exception as e:
			print("[Foreca] Error with fallback: %s" % e)

	def createSimpleMeteogramImage(self, output_path):
		"""Create a simple colored rectangle as meteogram placeholder"""
		try:
			from PIL import Image, ImageDraw

			# Create a simple image with text
			img = Image.new('RGB', (800, 400), color=(0, 0, 0))
			d = ImageDraw.Draw(img)

			# Add some text
			d.text((50, 50), "FORECA METEOGRAM", fill=(255, 255, 255))
			d.text((50, 100), "5-Day Weather Forecast", fill=(255, 255, 255))
			d.text((50, 150), "Data available but cannot display", fill=(255, 200, 200))
			d.text((50, 200), "graphical meteogram", fill=(255, 200, 200))

			img.save(output_path, 'PNG')
			print("[Foreca] Created simple meteogram placeholder")

		except Exception as e:
			print("[Foreca] Cannot create image: %s" % e)
			# Create empty file as last resort
			open(output_path, 'wb').close()

	def weatherMapSelected(self, result):
		"""Handle weather map selection"""
		if result:
			map_file = result[1]
			map_path = THUMB_PATH + map_file

			if exists(map_path):
				# Determina titolo in base alla mappa
				title_map = {
					"temp_map.png": _("Temperature Forecast"),
					"pressure_map.png": _("Pressure Forecast"),
					"cloud_map.png": _("Cloud Cover Forecast"),
					"sat_map.png": _("Satellite View"),
					"rain_map.png": _("Rain Radar"),
				}

				title = title_map.get(map_file, _("Weather Map"))
				full_title = f"{self.plaats} - {title}"

				print("[Foreca] Opening weather map: %s" % map_file)
				self.session.open(PicView, map_path, 0, False, full_title)
			else:
				self.session.open(MessageBox, _("Selected map not found"), MessageBox.TYPE_ERROR)

	def showMeteogram(self, devicepath):
		"""Show meteogram in main thread"""
		print("[Foreca] showMeteogram called with: %s" % devicepath)
		if exists(devicepath) and getsize(devicepath) > 0:
			self.session.open(PicView, devicepath, 0, False, str(self.plaats) + " - 5 Day Forecast")
		else:
			self.session.open(MessageBox, _("Meteogram file not found"), MessageBox.TYPE_ERROR)

	def showError(self, message):
		"""Show error in main thread"""
		print("[Foreca] showError: %s" % message)
		self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)


class CityPanelList(MenuList):

	def __init__(self, list, font0=22, font1=16, itemHeight=30, enableWrapAround=True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		GUIComponent.__init__(self)
		self.font0 = gFont("Regular", font0)
		self.font1 = gFont("Regular", font1)
		self.itemHeight = itemHeight
		self.foregroundColorSelected = 8900346
		self.foregroundColor = 0xffffff
		self.backgroundColorSelected = 0x565656
		self.column = 30

# ---------------------- get skin attribs ----------------------------
	def applySkin(self, desktop, parent):

		def font(value):
			self.font0 = parseFont(value, ((1, 1), (1, 1)))

		def font1(value):
			self.font1 = parseFont(value, ((1, 1), (1, 1)))

		def itemHeight(value):
			self.itemHeight = int(value)

		def foregroundColor(value):
			self.foregroundColor = parseColor(value).argb()

		def foregroundColorSelected(value):
			self.foregroundColorSelected = parseColor(value).argb()

		def backgroundColorSelected(value):
			self.backgroundColorSelected = parseColor(value).argb()

		def column(value):
			self.column = int(value)

		if self.skinAttributes:
			for (attrib, value) in list(self.skinAttributes):
				try:
					locals().get(attrib)(value)
					self.skinAttributes.remove((attrib, value))
				except Exception:
					pass
		self.l.setFont(0, self.font0)
		self.l.setFont(1, self.font1)
		self.l.setItemHeight(self.itemHeight)
		return GUIComponent.applySkin(self, desktop, parent)


class CityPanel(Screen, HelpableScreen):

	def __init__(self, session, panelmenu):
		self.session = session

		if size_w == 1920:
			self.skin = """
			<screen name="CityPanel" position="center,center" size="1200,900" title="Select a city">
					<eLabel backgroundColor="red" position="10,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="green" position="305,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="yellow" position="600,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="blue" position="895,65" size="295,6" zPosition="11" />
					<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
					<eLabel backgroundColor="#999999" position="10,80" size="1180,2" />
					<widget name="Mlist" itemHeight="35" position="10,90" size="1180,665" enableWrapAround="1" scrollbarMode="showOnDemand" />
					<eLabel backgroundColor="#999999" position="10,770" size="1180,2" />
					<ePixmap position="1025,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png" />
					<ePixmap position="379,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png" />
					<ePixmap position="42,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" />
					<ePixmap position="705,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png" />
					<ePixmap position="1085,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png" />
			</screen>"""

		elif size_w == 2560:
			self.skin = """
			<screen name="CityPanel" position="center,center" size="1600,1200" title="Select a city">
				<eLabel backgroundColor="red" position="14,87" size="394,8" zPosition="11"/>
				<eLabel backgroundColor="green" position="407,87" size="394,8" zPosition="11"/>
				<eLabel backgroundColor="yellow" position="800,87" size="394,8" zPosition="11"/>
				<eLabel backgroundColor="blue" position="1194,87" size="394,8" zPosition="11"/>
				<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#a08500" font="Regular;40" halign="center" position="800,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#18188b" font="Regular;40" halign="center" position="1194,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_blue" transparent="1" valign="center" zPosition="1"/>
				<eLabel backgroundColor="#999999" position="14,107" size="1574,3"/>
				<widget name="Mlist" itemHeight="47" position="14,120" size="1574,887" enableWrapAround="1" scrollbarMode="showOnDemand"/>
				<eLabel backgroundColor="#999999" position="14,1027" size="1574,3"/>
				<ePixmap position="1367,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
				<ePixmap position="506,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
				<ePixmap position="56,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
				<ePixmap position="940,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
				<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
				<ePixmap position="1447,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
			</screen>"""
		else:
			self.skin = """
			<screen name="CityPanel" position="center,center" size="800,600" title="Select a city">
				<eLabel backgroundColor="red" position="6,43" size="196,4" zPosition="11"/>
				<eLabel backgroundColor="green" position="203,43" size="196,4" zPosition="11"/>
				<eLabel backgroundColor="yellow" position="400,43" size="196,4" zPosition="11"/>
				<eLabel backgroundColor="blue" position="596,43" size="196,4" zPosition="11"/>
				<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#a08500" font="Regular;20" halign="center" position="400,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#18188b" font="Regular;20" halign="center" position="596,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_blue" transparent="1" valign="center" zPosition="1"/>
				<eLabel backgroundColor="#999999" position="6,53" size="786,1"/>
				<widget name="Mlist" itemHeight="23" position="6,60" size="786,443" enableWrapAround="1" scrollbarMode="showOnDemand"/>
				<eLabel backgroundColor="#999999" position="6,513" size="786,1"/>
				<ePixmap position="683,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
				<ePixmap position="252,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
				<ePixmap position="28,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
				<ePixmap position="470,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
				<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
				<ePixmap position="723,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
			</screen>"""

		Screen.__init__(self, session)
		self.setup_title = _("Select a city")
		self.Mlist = []
		self["Mlist"] = CityPanelList([])

		self.city = panelmenu
		self["key_green"] = StaticText(_("Favorite 1"))
		self["key_yellow"] = StaticText(_("Favorite 2"))
		self["key_blue"] = StaticText(_("Home"))
		self["key_ok"] = StaticText(_("Forecast"))
		self["key_red"] = StaticText(_("Keyboard"))
		self.setTitle(_("Select a city"))

		self.filtered_list = []
		self.search_text = ""
		self.search_ok = False

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"text": (self.openKeyboard, _("Keyboard")),
				"cancel": (self.exit, _("Exit - End")),
				"red": (self.openKeyboard, _("Open Keyboard")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"ok": (self.ok, _("OK - Select")),
				"green": (self.green, _("Green - Assign to Favorite 1")),
				"yellow": (self.yellow, _("Yellow - Assign to Favorite 2")),
				"blue": (self.blue, _("Blue - Assign to Home")),
				"nextBouquet": (self.jump500_down, _("Channel+ - 500 back")),
				"prevBouquet": (self.jump500_up, _("Channel- - 500 forward")),
				"volumeDown": (self.jump100_up, _("Volume- - 100 forward")),
				"volumeUp": (self.jump100_down, _("Volume+ - 100 back")),
				"showEventInfo": (self.info, _("Info - Legend")),
			},
			-2
		)
		self.onShown.append(self.prepare)

	def info(self):
		message = str("%s" % (_(
			"Server URL:    %s\n"
		) % BASEURL))
		entries = [
			(_("Server URL"), BASEURL),
			(_("VERSION"), VERSION),
			(_("Wind direction"), _("Arrow to right: Wind from the West")),
			(_("Ok"), _("Go to Config Plugin")),
			(_("Red"), _("Temperature chart for the upcoming 5 days")),
			(_("Green"), _("Go to Favorite 1")),
			(_("Yellow"), _("Go to Favorite 2")),
			(_("Blue"), _("Go to Home")),
			(_("Tv/Txt"), _("Go to City Panel")),
			# (_("Menu"), _("Satellite photos and maps")),
			(_("Up/Down"), _("Previous/Next page")),
			(_("<   >"), _("Prognosis Previous/Next day")),
			(_("0 - 9"), _("Prognosis (x) days from now"))
		]
		message += format_message(entries)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

	def openKeyboard(self):
		from Screens.VirtualKeyBoard import VirtualKeyBoard
		self.session.openWithCallback(
			self.filter,
			VirtualKeyBoard,
			title=_("Search your City"),
			text='')

	def filter(self, result):
		if result:
			try:
				self.filtered_list = []
				search_term = result.lower()
				for item in self.Mlist:
					city_name = item[0][0]
					if search_term in city_name.lower():
						self.search_ok = True
						self.filtered_list.append(item)
				if len(self.filtered_list) < 1:
					self.session.open(MessageBox, _('No City found in search!!!'), MessageBox.TYPE_INFO, timeout=5)
					return
				else:
					self['Mlist'].l.setList(self.filtered_list)
					self['Mlist'].moveToIndex(0)
					self["Mlist"].selectionEnabled(1)
			except Exception as error:
				print(error)
				self.session.open(MessageBox, _('An error occurred during search!'), MessageBox.TYPE_ERROR, timeout=5)

	def prepare(self):
		self.maxidx = 0
		self.Mlist = []
		if exists(USR_PATH + "/City.cfg"):
			with open(USR_PATH + "/City.cfg", "r") as content:
				for line in content:
					text = line.strip()
					self.maxidx += 1
					entry = (text.replace("_", " "), text)
					self.Mlist.append(self.CityEntryItem(entry))

		self.filtered_list = self.Mlist
		self["Mlist"].l.setList(self.filtered_list)
		self["Mlist"].selectionEnabled(1)

	def jump500_up(self):
		cur = self["Mlist"].l.getCurrentSelectionIndex()
		if (cur + 500) <= self.maxidx:
			self["Mlist"].instance.moveSelectionTo(cur + 500)
		else:
			self["Mlist"].instance.moveSelectionTo(self.maxidx - 1)

	def jump500_down(self):
		cur = self["Mlist"].l.getCurrentSelectionIndex()
		if (cur - 500) >= 0:
			self["Mlist"].instance.moveSelectionTo(cur - 500)
		else:
			self["Mlist"].instance.moveSelectionTo(0)

	def jump100_up(self):
		cur = self["Mlist"].l.getCurrentSelectionIndex()
		if (cur + 100) <= self.maxidx:
			self["Mlist"].instance.moveSelectionTo(cur + 100)
		else:
			self["Mlist"].instance.moveSelectionTo(self.maxidx - 1)

	def jump100_down(self):
		cur = self["Mlist"].l.getCurrentSelectionIndex()
		if (cur - 100) >= 0:
			self["Mlist"].instance.moveSelectionTo(cur - 100)
		else:
			self["Mlist"].instance.moveSelectionTo(0)

	def up(self):
		self["Mlist"].up()
		self["Mlist"].selectionEnabled(1)

	def down(self):
		self["Mlist"].down()
		self["Mlist"].selectionEnabled(1)

	def left(self):
		self["Mlist"].pageUp()

	def right(self):
		self["Mlist"].pageDown()

	def deactivateCacheDialog(self):
		self.cacheDialog.stop()
		self.working = False

	def exit(self):
		if self.search_ok is True:
			self.search_ok = False
		self.close(self.city)

	def ok(self):
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		print("OK city= %s" % self.city, "CurrentSelection= %s" % self['Mlist'].l.getCurrentSelection())
		if DEBUG:
			FAlog("city= %s" % self.city, "CurrentSelection= %s" % self['Mlist'].l.getCurrentSelection())

		self.close(self.city)

	def blue(self):
		global start
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		if DEBUG:
			FAlog("Home:", self.city)
		config.plugins.foreca.home.setValue(self.city)
		config.plugins.foreca.home.save()
		configfile.save()
		start = self.city[self.city.rfind("/") + 1:]
		message = "%s %s" % (_("This city is stored as home!\n\n                                  "), self.city)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=8)

	def green(self):
		global fav1
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		if DEBUG:
			FAlog("Fav1:", self.city)
		config.plugins.foreca.fav1.setValue(self.city)
		config.plugins.foreca.fav1.save()
		configfile.save()
		fav1 = self.city[self.city.rfind("/") + 1:]
		message = "%s %s" % (_("This city is stored as favorite 1!\n\n                             "), self.city)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=8)

	def yellow(self):
		global fav2
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		if DEBUG:
			FAlog("Fav2:", self.city)
		config.plugins.foreca.fav2.setValue(self.city)
		config.plugins.foreca.fav2.save()
		configfile.save()
		fav2 = self.city[self.city.rfind("/") + 1:]
		message = "%s %s" % (_("This city is stored as favorite 2!\n\n                             "), self.city)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=8)

	def CityEntryItem(self, entry):
		mblau = self["Mlist"].foregroundColorSelected
		weiss = self["Mlist"].foregroundColor
		grau = self["Mlist"].backgroundColorSelected
		itemHeight = self["Mlist"].itemHeight
		col = self["Mlist"].column
		res = [entry]
		res.append(MultiContentEntryText(pos=(0, 0), size=(col, itemHeight), font=0, text="", color=weiss, color_sel=mblau, backcolor_sel=grau, flags=RT_VALIGN_CENTER))
		res.append(MultiContentEntryText(pos=(col, 0), size=(1000, itemHeight), font=0, text=entry[0], color=weiss, color_sel=mblau, backcolor_sel=grau, flags=RT_VALIGN_CENTER))
		return res


class PicView(Screen):

	def __init__(self, session, filelist, index, startslide, plaats=None):
		self.session = session
		self.bgcolor = config.plugins.foreca.bgcolor.value
		space = config.plugins.foreca.framesize.value
		space = space + 5
		self.skin = "<screen name=\"PicView\" title=\"PicView\" position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" > \
					<!-- <eLabel position=\"0,0\" zPosition=\"-1\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.bgcolor + "\" /> --> \
					<widget name=\"pic\" position=\"" + str(space) + ", 50" + "\" size=\"" + str(size_w - (space * 2)) + "," + str(size_h - (space * 2)) + "\" zPosition=\"1\" alphatest=\"blend\" /> \
					<widget name=\"city\" position=\"" + str(space) + ", 20" + "\" font=\"Regular;34\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.bgcolor + "\" foregroundColor=\"#ffffff\" zPosition=\"10\" transparent=\"1\" /> \
					</screen>"

		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"stop": (self.Exit, _("Exit - End")),
			},
			-1
		)
		self["pic"] = Pixmap()
		self["city"] = Label(plaats)
		self.filelist = filelist
		self.startslide = startslide
		self.old_index = 0
		self.lastindex = index
		self.currPic = []
		self.setTitle(plaats)
		self.shownow = True
		self.dirlistcount = 0
		self.index = 0
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.finish_decode)
		self.onLayoutFinish.append(self.setPicloadConf)

	def setPicloadConf(self):
		sc = getScale()
		if not sc or len(sc) < 2:
			sc = (1920, 1080)
		if not hasattr(self, 'bgcolor') or not self.bgcolor:
			self.bgcolor = "#000000"
		resize_value = int(config.plugins.foreca.resize.value) if str(config.plugins.foreca.resize.value).isdigit() else 1
		self.picload.setPara([
			self["pic"].instance.size().width(),
			self["pic"].instance.size().height(),
			sc[0],
			sc[1],
			0,
			resize_value,
			self.bgcolor
		])
		self.start_decode()

	def ShowPicture(self):
		if self.shownow and len(self.currPic):
			self.shownow = False
			if self.currPic[0]:
				print("[ShowPicture] Imposto l'immagine:", self.currPic[0])
				self["pic"].instance.setPixmap(self.currPic[0].__deref__())
			else:
				print("[ShowPicture] No image data present.")

	def finish_decode(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr is not None:
			print("[finish_decode] Image data loaded successfully.")
			try:
				# remove_icc_profile(ptr)
				self.currPic = []
				self.currPic.append(ptr)
				self.ShowPicture()
			except Exception as e:
				print("[finish_decode] Errore:", str(e))
		else:
			print("[finish_decode] No image data obtained from picload.")

	def start_decode(self):
		self.picload.startDecode(self.filelist)

	def clear_images(self):
		try:
			if exists(self.filelist):
				remove(self.filelist)
			print("File immagine rimosso:", self.filelist)
			if exists(CACHE_PATH):
				for filename in listdir(CACHE_PATH):
					if filename.endswith(".jpg") or filename.endswith(".png"):
						file_path = join(CACHE_PATH, filename)
						try:
							remove(file_path)
							print("Image file removed:", file_path)
						except OSError as e:
							print("Error while removing file:", file_path, e)
		except Exception as e:
			print("Errore durante la rimozione del file:", e)

	def Exit(self):
		del self.picload
		self.clear_images()
		self.close(self.lastindex + self.dirlistcount)


class PicSetup(Screen, ConfigListScreen):

	if size_w == 1920:
		skin = """
		<screen name="PicSetup" position="center,center" size="1200,900" title="Setup">
			<eLabel backgroundColor="red" position="10,65" size="295,6" zPosition="11" />
			<eLabel backgroundColor="green" position="305,65" size="295,6" zPosition="11" />
			<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
			<eLabel backgroundColor="#999999" position="10,80" size="1180,2" />
			<widget enableWrapAround="1" name="Mlist" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
			<eLabel backgroundColor="#999999" position="10,770" size="1180,2" />
			<ePixmap position="42,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" />
			<widget backgroundColor="background" font="Regular;34" halign="right" position="1012,41" render="Label" shadowColor="black" shadowOffset="-2,-2" size="120,40" source="global.CurrentTime" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget backgroundColor="background" font="Regular;34" halign="right" position="730,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="400,40" source="global.CurrentTime" transparent="1">
				<convert type="ClockToText">Date</convert>
			</widget>
		</screen>"""

	elif size_w == 2560:
		skin = """
		<screen name="PicSetup" position="center,center" size="1600,1200" title="Setup">
			<eLabel backgroundColor="red" position="14,87" size="394,8" zPosition="11"/>
			<eLabel backgroundColor="green" position="407,87" size="394,8" zPosition="11"/>
			<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
			<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
			<eLabel backgroundColor="#999999" position="14,107" size="1574,3"/>
			<widget enableWrapAround="1" name="Mlist" position="14,120" scrollbarMode="showOnDemand" size="1574,960"/>
			<eLabel backgroundColor="#999999" position="14,1027" size="1574,3"/>
			<ePixmap position="56,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
			<widget backgroundColor="background" font="Regular;46" halign="right" position="1350,55" render="Label" shadowColor="black" shadowOffset="-2,-2" size="160,54" source="global.CurrentTime" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget backgroundColor="background" font="Regular;46" halign="right" position="974,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="534,54" source="global.CurrentTime" transparent="1">
				<convert type="ClockToText">Date</convert>
			</widget>
		</screen>"""
	else:
		skin = """
		<screen name="PicSetup" position="center,center" size="800,600" title="Setup">
			<eLabel backgroundColor="red" position="6,43" size="196,4" zPosition="11"/>
			<eLabel backgroundColor="green" position="203,43" size="196,4" zPosition="11"/>
			<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
			<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
			<eLabel backgroundColor="#999999" position="6,53" size="786,1"/>
			<widget enableWrapAround="1" name="Mlist" position="6,60" scrollbarMode="showOnDemand" size="786,480"/>
			<eLabel backgroundColor="#999999" position="6,513" size="786,1"/>
			<ePixmap position="28,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
			<widget backgroundColor="background" font="Regular;22" halign="right" position="674,27" render="Label" shadowColor="black" shadowOffset="-2,-2" size="80,26" source="global.CurrentTime" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget backgroundColor="background" font="Regular;22" halign="right" position="486,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="266,26" source="global.CurrentTime" transparent="1">
				<convert type="ClockToText">Date</convert>
			</widget>
		</screen>"""
	if DEBUG:
		FAlog("Setup...")

	def __init__(self, session):
		self.skin = PicSetup.skin
		Screen.__init__(self, session)
		self.setup_title = _("Settings")
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"ok": (self.OKcity, _("OK - City")),
				"green": (self.save, _("Green - Save")),
				"cancel": (self.cancel, _("Exit - End")),
				"red": (self.cancel, _("Exit - End")),
				"left": (self.keyLeft, _("Left")),
				"right": (self.keyRight, _("Right")),
				"up": (self.keyUp, _("Up")),
				"down": (self.keyDown, _("Down ")),
				"0": (boundFunction(self.keyNumberGlobal, 0), _("0")),
				"1": (boundFunction(self.keyNumberGlobal, 1), _("1")),
				"2": (boundFunction(self.keyNumberGlobal, 2), _("2")),
				"3": (boundFunction(self.keyNumberGlobal, 3), _("3")),
				"4": (boundFunction(self.keyNumberGlobal, 4), _("4")),
				"5": (boundFunction(self.keyNumberGlobal, 5), _("5")),
				"6": (boundFunction(self.keyNumberGlobal, 6), _("6")),
				"7": (boundFunction(self.keyNumberGlobal, 7), _("7")),
				"8": (boundFunction(self.keyNumberGlobal, 8), _("8")),
				"9": (boundFunction(self.keyNumberGlobal, 9), _("9")),
			},
			-3
		)

		self.list = []
		self.onChangedEntry = []
		self["Mlist"] = ConfigList(self.list)
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
		self.createSetup()
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.editListEntry = None
		self.list = []
		self.list.append(getConfigListEntry(_("Select units"), config.plugins.foreca.units))
		self.list.append(getConfigListEntry(_("Select time format"), config.plugins.foreca.time))
		self.list.append(getConfigListEntry(_("City names as labels in the Main screen"), config.plugins.foreca.citylabels))
		self.list.append(getConfigListEntry(_("Home City at start"), config.plugins.foreca.home))
		self.list.append(getConfigListEntry(_("Fav1 City"), config.plugins.foreca.fav1))
		self.list.append(getConfigListEntry(_("Fav2 City"), config.plugins.foreca.fav2))
		self.list.append(getConfigListEntry(_("Frame size in full view"), config.plugins.foreca.framesize))
		self.list.append(getConfigListEntry(_("Font size in slideshow"), config.plugins.foreca.fontsize))
		self.list.append(getConfigListEntry(_("Scaling Mode"), config.plugins.foreca.resize))
		self.list.append(getConfigListEntry(_("Slide Time (seconds)"), config.plugins.foreca.slidetime))
		self.list.append(getConfigListEntry(_("Show Infoline"), config.plugins.foreca.infoline))
		self.list.append(getConfigListEntry(_("Textcolor"), config.plugins.foreca.textcolor))
		self.list.append(getConfigListEntry(_("Backgroundcolor"), config.plugins.foreca.bgcolor))
		self.list.append(getConfigListEntry(_("Slide picture in loop"), config.plugins.foreca.loop))
		self.list.append(getConfigListEntry(_("Display in extensions menu"), config.plugins.foreca.extmenu))
		self.list.append(getConfigListEntry(_("Debug"), config.plugins.foreca.debug))
		self["Mlist"].list = self.list
		self["Mlist"].l.setList(self.list)

	def OKcity(self):
		current_item = str(self["Mlist"].getCurrent()[1].getText())
		self.config_entry = None

		if current_item == config.plugins.foreca.home.value:
			self.config_entry = config.plugins.foreca.home
		elif current_item == config.plugins.foreca.fav1.value:
			self.config_entry = config.plugins.foreca.fav1
		elif current_item == config.plugins.foreca.fav2.value:
			self.config_entry = config.plugins.foreca.fav2

		if self.config_entry is None:
			print("ERROR: self.config_entry is None in OKcity!")
			return

		self.session.openWithCallback(self.OKCallback, CityPanel, self.config_entry)

	def OKCallback(self, city=None):
		print("Received city:", city)

		if city is None:
			print("No city selected, exiting callback.")
			return

		if not isinstance(city, str):
			print("ERROR: city is not a string! Current type:", type(city))
			return

		city_parts = city.split("/")
		if len(city_parts) == 2:
			country, city_name = city_parts
			print("Country:", country)
			print("City:", city_name)
		else:
			print("ERROR: city format is incorrect")
			return

		if not isinstance(self.config_entry, ConfigText):
			print("WARNING: self.config_entry was lost or corrupted. Restoring it.")
			self.config_entry = config.plugins.foreca.home

		if self.config_entry is None:
			print("ERROR: self.config_entry is still None after restoring!")
			return

		if not callable(getattr(self.config_entry, "setValue", None)):
			print("ERROR: setValue is not callable! It is:", type(self.config_entry.setValue))
			return

		try:
			self.config_entry.setValue(city)
			self.config_entry.save()
		except Exception as e:
			print("Unexpected error:", e)
		configfile.save()
		self.city = city
		self.createSetup()

	def changedEntry(self):
		current_item = self["Mlist"].getCurrent()
		if current_item is not None:
			self.item = current_item
			for callback in self.onChangedEntry:
				callback()
			config_item = current_item[1]
			if isinstance(config_item, (ConfigYesNo, ConfigText, ConfigSelection, ConfigEnableDisable)):
				self.createSetup()
		else:
			print("Errore: No element select in Mlist!")

	def getCurrentEntry(self):
		return self["Mlist"].getCurrent() and self["Mlist"].getCurrent()[0] or ""

	def getCurrentValue(self):
		return self["Mlist"].getCurrent() and str(self["Mlist"].getCurrent()[1].getText()) or ""

	def save(self):
		if self["Mlist"].isChanged():
			for x in self["Mlist"].list:
				x[1].save()
			config.save()
		self.refreshPlugins()
		self.close()

	def cancel(self):
		for x in self["Mlist"].list:
			x[1].cancel()
		self.close()

	def keyLeft(self):
		self["Mlist"].handleKey(KEY_LEFT)
		self.createSetup()

	def keyRight(self):
		self["Mlist"].handleKey(KEY_RIGHT)
		self.createSetup()

	def keyDown(self):
		self['Mlist'].instance.moveSelection(self['Mlist'].instance.moveDown)
		self.createSetup()

	def keyUp(self):
		self['Mlist'].instance.moveSelection(self['Mlist'].instance.moveUp)
		self.createSetup()

	def keyNumberGlobal(self, number):
		self["Mlist"].handleKey(KEY_0 + number)
		self.createSetup()

	def refreshPlugins(self):
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
