# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from . import _, file_url  # , isDreambox
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.ConfigList import ConfigList
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
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
from datetime import datetime, timedelta
from enigma import (
	eListboxPythonMultiContent,
	ePicLoad,
	eTimer,
	getDesktop,
	gFont,
	RT_VALIGN_CENTER,
)
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CONFIG, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from locale import setlocale, LC_COLLATE, strxfrm
from os import makedirs, unlink, remove, listdir
from os.path import exists, join
from re import sub, DOTALL, compile, findall
from skin import parseFont, parseColor
from sys import version_info
from time import strftime
from twisted.internet._sslverify import ClientTLSOptions
from twisted.internet.ssl import ClientContextFactory
import requests
import ssl
import warnings

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


try:
	from PIL import Image
except ImportError:
	from Image import Image


if PY3:
	from io import BytesIO
else:
	from cStringIO import StringIO as BytesIO


try:
	_create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
	pass
else:
	ssl._create_default_https_context = _create_unverified_https_context


try:
	unicode
except NameError:
	unicode = str  # In Python 3, unicode == str

VERSION = "3.3.7"


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
#                 31.12.2024
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


class WebClientContextFactory(ClientContextFactory):
	def __init__(self, url=None):
		domain = urlparse(url).netloc
		self.hostname = domain

	def getContext(self, hostname=None, port=None):
		ctx = ClientContextFactory.getContext(self)
		if self.hostname and ClientTLSOptions is not None:  # workaround for TLS SNI
			ClientTLSOptions(self.hostname, ctx)
		return ctx


languages = [
	("no", "NO (Default)"),
	("com", "English"),
	("ba", "Bosnia ed Erzegovina"),
	("nz", "New Zealand"),
	("bg", "българск"),
	("cs", "Čeština"),
	("da", "Dansk"),
	("de", "Deutsch"),
	("com/el", "ελληνικά"),
	("es", "Español"),
	("et", "Eesti"),
	("https://www.farsiweather.com/", "زبان فارسی"),
	("fr", "Français"),
	("hr", "Hrvatski"),
	("in", "तब"),
	("it", "Italiano"),
	("lv", "Latviešu"),
	("hu", "Magyar"),
	("nl", "Nederlands"),
	("pl", "Polski"),
	("pt", "Português"),
	("ro", "Româneşte"),
	("ru", "Русский"),
	("sk", "Slovenčina"),
	("fi", "Suomi"),
	("sv", "Svenska"),
	("tr", "Türkçe"),
]

pluginPrintname = "[Foreca Ver. %s]" % VERSION
# config.plugins.foreca.languages = ConfigSelection(default="no", choices=languages)
config.plugins.foreca.home = ConfigText(default="Germany/Berlin", fixed_size=False)
config.plugins.foreca.fav1 = ConfigText(default="United_States/New_York/New_York_City", fixed_size=False)
config.plugins.foreca.fav2 = ConfigText(default="Japan/Tokyo", fixed_size=False)
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
config.plugins.foreca.debug = ConfigEnableDisable(default=False)

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6'}


def get_base_url_from_txt(file_url, fallback_url="https://www.foreca.ba/"):
	"""
	Reads a new URL base from a .txt file hosted on a site.
	If it fails to get the content or the URL is invalid, it uses a fallback URL base.
	:param file_url: URL of the .txt file that contains the new URL base
	:param fallback_url: URL to use if an error occurs
	:return: The URL base obtained from the .txt file or the fallback URL
	"""
	try:
		response = requests.get(file_url, timeout=10)
		response.raise_for_status()
		new_base_url = response.text.strip()
		test_response = requests.get(new_base_url, timeout=10)
		test_response.raise_for_status()
		print("New URL base found and working:", new_base_url)
		return new_base_url
	except Exception as e:
		print("Error reading base URL from file .txt:", str(e))
		print("Using the fallback URL base:", fallback_url)
		return fallback_url


lng = 'en'
try:
	lng = config.osd.language.value
	lng = lng[:-3]
except:
	lng = 'en'
	pass

"""
# def detect_system_language():
	# try:
		# from Components.config import config
		# lng = config.osd.language.value
		# return lng.split('_')[0] if '_' in lng else lng
	# except (ImportError, AttributeError, KeyError):
		# return lng

# detect_system_language()
"""

"""
selected_language = config.plugins.foreca.languages.value
if not selected_language == 'no':
	if selected_language == "https://www.farsiweather.com/":
		BASEURL = selected_language  # URL specifico per il Farsi
	else:
		BASEURL = 'https://www.foreca.' + selected_language
else:
	BASEURL = get_base_url_from_txt(file_url)
"""
BASEURL = get_base_url_from_txt(file_url)
if not BASEURL.endswith("/"):
	BASEURL += "/"

MODULE_NAME = __name__.split(".")[-1]
MAIN_PAGE = BASEURL.rstrip("/")
USR_PATH = resolveFilename(SCOPE_CONFIG) + "Foreca"
PICON_PATH = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/picon/"
THUMB_PATH = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/thumb/"
print("BASEURL in uso:", BASEURL)


DEBUG = config.plugins.foreca.debug.value
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


def FAlog(info, wert=""):
	if config.plugins.foreca.debug.value:
		try:
			with open('/tmp/foreca.log', 'a') as f:
				f.write('{} {} {}\r\n'.format(strftime('%H:%M:%S'), info, wert))
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


def remove_icc_profile(devicepath):
	try:
		warnings.filterwarnings("ignore", "(?s).*iCCP.*", category=UserWarning)
		img = Image.open(devicepath)
		img.save(devicepath, icc_profile=None)
	except Exception as e:
		print("Error: Failed to remove ICC profile", str(e))
		raise e


def getScale():
	return AVSwitch().getFramebufferScale()


def clean_url(url):
	return url.replace('\ufeff', '')


# ------------------------------------------------------------------------------------------
# ----------------------------------  MainMenuList   ---------------------------------------
# ------------------------------------------------------------------------------------------


class MainMenuList(MenuList):

	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		GUIComponent.__init__(self)
		# default values:
		self.font0 = gFont("Regular", 28)
		self.font1 = gFont("Regular", 26)
		self.font2 = gFont("Regular", 28)
		self.font3 = gFont("Regular", 28)

		self.itemHeight = 150
		self.valTime = 5, 80, 100, 45
		self.valPict = 120, 45, 70, 70
		self.valPictScale = 1
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

# --------------------------- get skin attribs ---------------------------------------------
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

# --------------------------- Go through all list entries ----------------------------------
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

# ----------------------------------- Build entries for list -------------------------------

	def buildEntry(self, picInfo=None):


		self.x = self.list[self.idx]
		self.res = [(self.x[0], self.x[1])]

		violetred = 0xC7D285
		violet = 0xff40b3
		gruen = 0x77f424
		dgruen = 0x53c905
		drot = 0xff4040
		rot = 0xff6640
		orange = 0xffb340
		gelb = 0xffff40
		ddblau = 0x3b62ff
		dblau = 0x408cff
		mblau = 0x40b3ff
		blau = 0x40d9ff
		hblau = 0x40ffff
		weiss = 0xffffff

		if config.plugins.foreca.units.value == "us":
			self.centigrades = round((int(self.x[2]) - 32) / 1.8)
			tempUnit = "°F"
		else:
			self.centigrades = int(self.x[2])
			tempUnit = "°C"
		if self.centigrades <= -20:
			self.tempcolor = ddblau
		elif self.centigrades <= -15:
			self.tempcolor = dblau
		elif self.centigrades <= -10:
			self.tempcolor = mblau
		elif self.centigrades <= -5:
			self.tempcolor = blau
		elif self.centigrades <= 0:
			self.tempcolor = hblau
		elif self.centigrades < 5:
			self.tempcolor = dgruen
		elif self.centigrades < 10:
			self.tempcolor = gruen
		elif self.centigrades < 15:
			self.tempcolor = gelb
		elif self.centigrades < 20:
			self.tempcolor = orange
		elif self.centigrades < 25:
			self.tempcolor = rot
		elif self.centigrades < 30:
			self.tempcolor = drot
		else:
			self.tempcolor = violet

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
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=3, text=self.x[2] + tempUnit, color=self.tempcolor, color_sel=self.tempcolor))

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
		self.res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=2, text=textsechs, color=mblau, color_sel=mblau))

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


# ------------------------------------------------------------------------------------------
# ------------------------------------------ Spinner ---------------------------------------
# ------------------------------------------------------------------------------------------


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
		# self.timer.callback.append(self.showNextSpinner)
		try:
			self.timer.callback.append(self.showNextSpinner)
		except:
			self.timer_conn = self.timer.timeout.connect(self.showNextSpinner)

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

# ------------------------------------------------------------------------------------------
# ------------------------------ Foreca Preview---------------------------------------------
# ------------------------------------------------------------------------------------------


class ForecaPreview(Screen, HelpableScreen):

	def __init__(self, session):
		global MAIN_PAGE, menu
		self.session = session
		now = datetime.now()
		heute = now.strftime("%Y%m%d")

		if DEBUG:
			FAlog("determined local date:", str(heute))

		self.tag = 0

		# Get favorites
		global fav1, fav2, city, start
		fav1 = config.plugins.foreca.fav1.value
		fav1 = fav1[fav1.rfind("/") + 1:]
		print(pluginPrintname, "fav1 location:", fav1)
		fav2 = config.plugins.foreca.fav2.value
		fav2 = fav2[fav2.rfind("/") + 1:]
		print(pluginPrintname, "fav2 location:", fav2)
		# Get home location
		self.ort = config.plugins.foreca.home.value
		start = self.ort[self.ort.rfind("/") + 1:]
		# print(pluginPrintname, "Start Home location:", start)
		MAIN_PAGE = "%s%s?lang=%s&details=%s&units=%s&tf=%s" % (
			BASEURL,
			pathname2url(self.ort),
			LANGUAGE,
			heute,
			config.plugins.foreca.units.value,
			config.plugins.foreca.time.value
		)
		"""
		# if isinstance(MAIN_PAGE, unicode):
			# MAIN_PAGE = MAIN_PAGE.encode('utf-8')
		"""
		if DEBUG:
			FAlog("initial link:", MAIN_PAGE)

		if size_w == 1920:
			self.skin = """
				<screen name="ForecaPreview" position="center,center" size="1200,900" title="Foreca Weather Forecast">
					<eLabel backgroundColor="red" cornerRadius="3" position="10,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="green" cornerRadius="3" position="305,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="yellow" cornerRadius="3" position="600,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="blue" cornerRadius="3" position="895,65" size="295,6" zPosition="11" />
					<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
					<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
					<widget backgroundColor="background" source="Titel" render="Label" position="13,775" size="1180,40" foregroundColor="yellow" font="Regular;32" halign="center" transparent="1" />
					<widget backgroundColor="background" source="Titel2" render="Label" position="13,123" size="1180,40" font="Regular;32" halign="center" transparent="1" />
					<widget backgroundColor="background" source="Titel3" render="Label" position="13,84" size="1180,40" foregroundColor="yellow" font="Regular;32" halign="center" transparent="1" />
					<widget backgroundColor="background" source="Titel4" render="Label" position="13,818" size="1180,40" font="Regular;32" halign="center" transparent="1" />
					<widget name="MainList" position="13,165" size="1180,600" zPosition="3" foregroundColor="#ffffff" backgroundColor="#000000" foregroundColorSelected="#ffffff" backgroundColorSelected="barColor" alphatest="1" font0="Regular;30" font1="Fixed;30" font2="Fixed;28" font3="Regular;30" itemHeight="200" setTime="15,40,100,45" setPict="150,40,70,70" setPictScale="1" setTemp="280,50,200,40" setTempUnits="280,95,150,40" setWindPict="550,75,35,35" setWindPictScale="1" setWind="600,50,95,40" setWindUnits="600,95,50,40" text1Pos="720,0,600,42" text2Pos="720,50,600,42" text3Pos="720,100,600,42" text4Pos="720,150,600,42" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1" />
					<eLabel backgroundColor="grey" position="10,770" size="1180,1" />
					<ePixmap position="1025,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png" />
					<ePixmap position="379,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png" />
					<ePixmap position="42,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" />
					<ePixmap position="705,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png" />
					<ePixmap position="1085,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_help.png" />
					<widget source="key_info" render="Label" position="771,864" size="250,35" font="Regular;30" />
					<widget source="key_menu" render="Label" position="441,864" size="250,35" font="Regular;30" />
					<widget source="key_ok" render="Label" position="104,864" size="250,35" font="Regular;30" />
				</screen>"""
		elif size_w == 2560:
			self.skin = """
				<screen name="ForecaPreview" position="center,center" size="1600,1200" title="Foreca Weather Forecast">
					<eLabel backgroundColor="red" cornerRadius="3" position="14,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="green" cornerRadius="3" position="407,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="yellow" cornerRadius="3" position="800,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="blue" cornerRadius="3" position="1194,87" size="394,8" zPosition="11"/>
					<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#a08500" font="Regular;40" halign="center" position="800,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#18188b" font="Regular;40" halign="center" position="1194,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="grey" position="14,107" size="1574,2"/>
					<widget backgroundColor="background" source="Titel" render="Label" position="18,1034" size="1574,54" foregroundColor="yellow" font="Regular;43" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel2" render="Label" position="18,164" size="1574,54" font="Regular;43" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel3" render="Label" position="18,112" size="1574,54" foregroundColor="yellow" font="Regular;43" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel4" render="Label" position="18,1091" size="1574,54" font="Regular;43" halign="center" transparent="1"/>
					<widget name="MainList" position="18,220" size="1574,800" zPosition="3" foregroundColor="#ffffff" backgroundColor="#000000" foregroundColorSelected="#ffffff" backgroundColorSelected="barColor" alphatest="1" font0="Regular;30" font1="Fixed;30" font2="Fixed;28" font3="Regular;30" itemHeight="267" setTime="15,40,100,45" setPict="150,40,70,70" setPictScale="1" setTemp="280,50,200,40" setTempUnits="280,95,150,40" setWindPict="550,75,35,35" setWindPictScale="1" setWind="600,50,95,40" setWindUnits="600,95,50,40" text1Pos="720,0,600,42" text2Pos="720,50,600,42" text3Pos="720,100,600,42" text4Pos="720,150,600,42" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1"/>
					<eLabel backgroundColor="grey" position="14,1027" size="1574,2"/>
					<ePixmap position="1367,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
					<ePixmap position="506,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
					<ePixmap position="56,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="940,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
					<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="1447,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
					<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_help.png"/>
					<widget source="key_info" render="Label" position="1028,1152" size="334,47" font="Regular;40"/>
					<widget source="key_menu" render="Label" position="588,1152" size="334,47" font="Regular;40"/>
					<widget source="key_ok" render="Label" position="139,1152" size="334,47" font="Regular;40"/>
				</screen>"""
		else:
			self.skin = """
				<screen name="ForecaPreview" position="center,center" size="800,600" title="Foreca Weather Forecast">
					<eLabel backgroundColor="red" cornerRadius="3" position="6,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="green" cornerRadius="3" position="203,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="yellow" cornerRadius="3" position="400,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="blue" cornerRadius="3" position="596,43" size="196,4" zPosition="11"/>
					<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#a08500" font="Regular;20" halign="center" position="400,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#18188b" font="Regular;20" halign="center" position="596,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="grey" position="6,53" size="786,1"/>
					<widget backgroundColor="background" source="Titel" render="Label" position="8,516" size="786,26" foregroundColor="yellow" font="Regular;21" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel2" render="Label" position="8,82" size="786,26" font="Regular;21" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel3" render="Label" position="8,56" size="786,26" foregroundColor="yellow" font="Regular;21" halign="center" transparent="1"/>
					<widget backgroundColor="background" source="Titel4" render="Label" position="8,545" size="786,26" font="Regular;21" halign="center" transparent="1"/>
					<widget name="MainList" position="8,110" size="786,400" zPosition="3" foregroundColor="#ffffff" backgroundColor="#000000" foregroundColorSelected="#ffffff" backgroundColorSelected="barColor" alphatest="1" font0="Regular;30" font1="Fixed;30" font2="Fixed;28" font3="Regular;30" itemHeight="133" setTime="15,40,100,45" setPict="150,40,70,70" setPictScale="1" setTemp="280,50,200,40" setTempUnits="280,95,150,40" setWindPict="550,75,35,35" setWindPictScale="1" setWind="600,50,95,40" setWindUnits="600,95,50,40" text1Pos="720,0,600,42" text2Pos="720,50,600,42" text3Pos="720,100,600,42" text4Pos="720,150,600,42" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1"/>
					<eLabel backgroundColor="grey" position="6,513" size="786,1"/>
					<ePixmap position="683,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
					<ePixmap position="252,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
					<ePixmap position="28,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="470,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
					<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="723,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
					<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_help.png"/>
					<widget source="key_info" render="Label" position="514,576" size="166,23" font="Regular;20"/>
					<widget source="key_menu" render="Label" position="294,576" size="166,23" font="Regular;20"/>
					<widget source="key_ok" render="Label" position="69,576" size="166,23" font="Regular;20"/>
				</screen>"""

		Screen.__init__(self, session)
		self.setup_title = _("Foreca Weather Forecast")
		self["MainList"] = MainMenuList()
		self["Titel"] = StaticText()
		self["Titel2"] = StaticText(_("Please wait ..."))
		self["Titel3"] = StaticText()
		self["Titel4"] = StaticText()
		self["Titel5"] = StaticText()
		self["key_red"] = StaticText(_("Week"))
		self["key_ok"] = StaticText(_("Config"))
		if config.plugins.foreca.citylabels.value is True:
			self["key_green"] = StaticText(fav1.replace("_", " "))
			self["key_yellow"] = StaticText(fav2.replace("_", " "))
			self["key_blue"] = StaticText(start.replace("_", " "))
		else:
			self["key_green"] = StaticText(_("Favorite 1"))
			self["key_yellow"] = StaticText(_("Favorite 2"))
			self["key_blue"] = StaticText(_("Home"))
		self["key_info"] = StaticText(_("Legend"))
		self["key_menu"] = StaticText(_("Maps"))
		self.setTitle(_("Foreca Weather Forecast") + " " + _("Version ") + VERSION)
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"cancel": (self.exit, _("Exit - End")),
				"menu": (self.Menu, _("Menu - Weather maps")),
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
		self.StartPageFirst()

	def PicSetupMenu(self):
		self.session.openWithCallback(self.OKCallback, PicSetup)

	def StartPageFirst(self):
		if DEBUG:
			FAlog("StartPageFirst...")
		self.cacheDialog = self.session.instantiateDialog(ForecaPreviewCache)
		self["MainList"].callback = self.deactivateCacheDialog
		self.working = False
		self["MainList"].show
		self.cacheTimer = eTimer()
		self.cacheDialog.start()
		self.onLayoutFinish.append(self.getPage)

	def StartPage(self):
		self["Titel"].text = ""
		self["Titel3"].text = ""
		self["Titel4"].text = ""
		self["Titel5"].text = ""
		self["Titel2"].text = _("Please wait ...")
		self.working = False
		if DEBUG:
			FAlog("MainList show...")
		self["MainList"].show
		self.getPage()

	def getPage(self, page=None):
		if DEBUG:
			FAlog("getPage...")
		self.cacheDialog.start()
		self.working = True
		if not page:
			page = ""
		url = "%s%s" % (MAIN_PAGE, page)
		if DEBUG:
			FAlog("page link:", url)
		try:
			req = Request(url, headers=HEADERS)
			resp = urlopen(req, timeout=10)
			self.getForecaPage(resp.read().decode('utf-8') if PY3 else resp.read())
		except Exception as e:
			self.error(repr(e))
		self.deactivateCacheDialog()

	def error(self, err=""):
		if DEBUG:
			FAlog("getPage Error:", err)
		self.working = False
		self.deactivateCacheDialog()

	def deactivateCacheDialog(self):
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

	def Fav0(self):
		global start
		self.ort = config.plugins.foreca.home.value
		print("home location:", self.ort)
		start = self.ort[self.ort.rfind("/") + 1:]
		self.Zukunft(0)

	def Fav1(self):
		global fav1
		self.ort = config.plugins.foreca.fav1.value
		fav1 = self.ort[self.ort.rfind("/") + 1:]
		print(pluginPrintname, "fav1 location:", fav1)
		self.Zukunft(0)

	def Fav2(self):
		global fav2
		self.ort = config.plugins.foreca.fav2.value
		fav2 = self.ort[self.ort.rfind("/") + 1:]
		print(pluginPrintname, "fav2 location:", fav2)
		self.Zukunft(0)

	def futurdata(self, ztag=0):
		global MAIN_PAGE
		# Get the current date and time
		now = datetime.now()
		# Calculate new date by adding day tags
		future_date = now + timedelta(days=ztag)
		# Get the future date in the required format (YYYYMMDD)
		morgen = future_date.strftime("%Y%m%d")
		return morgen

	def Zukunft(self, ztag=0):
		global MAIN_PAGE
		morgen = self.futurdata(ztag)
		MAIN_PAGE = "%s%s?lang=%s&details=%s&units=%s&tf=%s" % (
			BASEURL,
			pathname2url(self.ort),
			LANGUAGE,
			morgen,
			config.plugins.foreca.units.value,
			config.plugins.foreca.time.value
		)
		# if isinstance(MAIN_PAGE, unicode):
			# MAIN_PAGE = MAIN_PAGE.encode('utf-8')
		if DEBUG:
			FAlog("day link:", MAIN_PAGE)
		# Show in GUI
		self.StartPage()

	def info(self):
		message = str("%s" % (_(
			"Server URL:    %s\n\n"
		) % BASEURL))
		message += _("<   >      =   Prognosis next/previous day\n")
		message += _("0 - 9      =   Prognosis (x) days from now\n\n")
		message += _("VOL+/-     =   Fast scroll 100 (City choice)\n")
		message += _("Bouquet+/- =   Fast scroll 500 (City choice)\n\n")
		message += _("Info       =   This information\n")
		message += _("Menu       =   Satellite photos and maps\n\n")
		message += _("Ok         =   Go to Config Plugin\n\n")
		message += _("Tv         =   Go to City Panel\n\n")
		message += _("Red        =   Temperature chart for the upcoming 5 days\n")
		message += _("Green      =   Go to Favorite 1\n")
		message += _("Yellow     =   Go to Favorite 2\n")
		message += _("Blue       =   Go to Home\n\n")
		message += _("Wind direction =   Arrow to right: Wind from the West\n")
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO)

	def OK(self):
		global city
		city = self.ort
		self.session.openWithCallback(self.OKCallback, CityPanel, city)

	def OKCallback(self, callback=None):
		global city, fav1, fav2
		self.tag = 0
		self.Zukunft(0)

		fav1 = str(config.plugins.foreca.fav1.value)
		fav2 = str(config.plugins.foreca.fav2.value)
		start = str(config.plugins.foreca.home.value)
		city = start
		self.ort = city

		if config.plugins.foreca.citylabels.value is True:
			self["key_green"].setText(fav1.replace("_", " "))
			self["key_yellow"].setText(fav2.replace("_", " "))
			self["key_blue"].setText(start.replace("_", " "))
		else:
			self["key_green"].setText(_("Favorite 1"))
			self["key_yellow"].setText(_("Favorite 2"))
			self["key_blue"].setText(_("Home"))

		if DEBUG:
			FAlog("MenuCallback")
		self.deactivateCacheDialog()

	def left(self):
		if not self.working and self.tag >= 1:
			self.tag = self.tag - 1
			self.Zukunft(self.tag)

	def right(self):
		if not self.working and self.tag < 9:
			self.tag = self.tag + 1
			self.Zukunft(self.tag)

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
		try:
			if not self.working:
				self.url = "%smeteogram.php?loc_id=%s&mglang=%s&units=%s&tf=%s/meteogram.png" % (BASEURL, self.loc_id, LANGUAGE, config.plugins.foreca.units.value, config.plugins.foreca.time.value)
				print('self.url=', self.url)
				self.loadPicture(self.url)
		except Exception as e:
			print('error red=', e)

	def Menu(self):
		self.session.openWithCallback(self.MenuCallback, SatPanel, self.ort)

	def MenuCallback(self):
		global menu, start, fav1, fav2
		fav1 = str(config.plugins.foreca.fav1.value)
		fav2 = str(config.plugins.foreca.fav2.value)
		start = str(config.plugins.foreca.home.value)
		city = start
		self.ort = city

		if config.plugins.foreca.citylabels.value is True:
			self["key_green"].setText(fav1.replace("_", " "))
			self["key_yellow"].setText(fav2.replace("_", " "))
			self["key_blue"].setText(start.replace("_", " "))
		else:
			self["key_green"].setText(_("Favorite 1"))
			self["key_yellow"].setText(_("Favorite 2"))
			self["key_blue"].setText(_("Home"))

	def loadPicture(self, url=""):
		devicepath = CACHE_PATH + "meteogram.png"
		req = Request(url, headers=HEADERS)
		resp = urlopen(req, timeout=10)
		with open(devicepath, 'wb') as f:
			f.write(resp.read())
		try:
			warnings.filterwarnings("ignore", "(?s).*iCCP.*", category=UserWarning)
			img = Image.open(devicepath)
			img.save(devicepath, icc_profile=None)
		except Exception as e:
			print("Errore nella rimozione del profilo ICC:", e)
		self.session.open(PicView, devicepath, 0, False)

	def getForecaPage(self, html):
		"""
		with open("/tmp/foreca_response.html", "w", encoding="utf-8") as f:
			f.write(html)
		"""
		fulltext = compile(r"id: '(.*?)'", DOTALL)
		id = fulltext.findall(html)
		if DEBUG:
			FAlog("fulltext= %s id= %s" % (fulltext, id))
		self.loc_id = str(id[0])
		# <!-- START -->
		if DEBUG:
			FAlog("Start:" + str(len(html)))
		fulltext = compile(r'<!-- START -->.+?<h6><span>(.+?)</h6>', DOTALL)
		titel = fulltext.findall(html)
		if DEBUG:
			FAlog("fulltext=%s titel= %s" % (fulltext, titel))

		titel[0] = str(sub(r'<[^>]*>', "", titel[0]))

		if DEBUG:
			FAlog("titel[0]=%s" % titel[0])

		def translate_description_gettext(description, translation_dict):
			cleaned_description = sub(r'[\t\r\n]', ' ', description).strip()
			words = sub(r'([.,!?])', r' \1 ', cleaned_description).split()
			translated_words = []
			for word in words:
				is_capitalized = word[0].isupper()
				translated_word = translation_dict.get(word.lower(), word)
				if is_capitalized:
					translated_word = translated_word.capitalize()
				translated_words.append(translated_word)
				print("translated_words=", translated_words)
			return ' '.join(translated_words)

		translation_dict = self.load_translation_dict(lng)
		# titel[0] = self.konvert_uml(str(sub(r'<[^>]*>', "", titel[0])))
		titel[0] = translate_description_gettext(titel[0], translation_dict)

		# <a href="/Austria/Linz?details=20110330">We</a>
		fulltext = compile(r'<!-- START -->(.+?)<h6>', DOTALL)
		link = str(fulltext.findall(html))
		# print('Link=', link)
		fulltext = compile(r'<a href=".+?>(.+?)<.+?', DOTALL)
		tag = str(fulltext.findall(link))
		# print "Day ", tag

		# ---------- Wetterdaten -----------

		# <div class="row clr0">
		fulltext = compile(r'<!-- START -->(.+?)<div class="datecopy">', DOTALL)
		html = str(fulltext.findall(html))
		if DEBUG:
			FAlog("searching .....")
		datalist = []

		fulltext = compile(r'<a href="(.+?)".+?', DOTALL)
		taglink = str(fulltext.findall(html))
		# taglink = konvert_uml(taglink)
		if DEBUG:
			FAlog("Daylink %s" % taglink)

		fulltext = compile(r'<a href=".+?>(.+?)<.+?', DOTALL)
		tag = fulltext.findall(html)

		if DEBUG:
			FAlog("Day=%s" % str(tag))

		# <div class="c0"> <strong>17:00</strong></div>
		fulltime = compile(r'<div class="c0"> <strong>(.+?)<.+?', DOTALL)
		zeit = fulltime.findall(html)
		if DEBUG:
			FAlog("Time=%s" % str(zeit))

		# <div class="c4">
		# <span class="warm"><strong>+15&deg;</strong></span><br />
		fulltime = compile(r'<div class="c4">.*?<strong>(.+?)&.+?', DOTALL)
		temp = fulltime.findall(html)

		if DEBUG:
			FAlog("Temp=%s" % str(temp))

		# <div class="symbol_50x50d symbol_d000_50x50" title="clear"

		fulltext = compile(r'<div class="symbol_50x50.+? symbol_(.+?)_50x50.+?', DOTALL)
		thumbnails = fulltext.findall(html)
		if DEBUG:
			FAlog("thumbnails=%s" % str(thumbnails))

		fulltext = compile(r'<div class="c3">.+? (.+?)<br />.+?', DOTALL)
		description = fulltext.findall(html)
		if DEBUG:
			FAlog("description=%s" % str(description).lstrip("\r\n\t").lstrip())

		fulltext = compile(r'<div class="c3">.+?<br />(.+?)</strong>.+?', DOTALL)
		feels = fulltext.findall(html)
		if DEBUG:
			FAlog("feels=%s" % str(feels).lstrip("\t").lstrip())

		fulltext = compile(r'<div class="c3">.+?</strong><br />(.+?)</.+?', DOTALL)
		precip = fulltext.findall(html)
		if DEBUG:
			FAlog("precip=%s" % str(precip).lstrip("\t").lstrip())

		fulltext = compile(r'<div class="c3">.+?</strong><br />.+?</strong><br />(.+?)</', DOTALL)
		humidity = fulltext.findall(html)
		if DEBUG:
			FAlog("humidity=%s" % str(humidity).lstrip("\t").lstrip())

		fulltext = compile(r'<div class="c2">.+?<img src="//img-b.foreca.net/s/symb-wind/(.+?).gif', DOTALL)
		windDirection = fulltext.findall(html)
		if DEBUG:
			FAlog("windDirection=%s" % str(windDirection))

		fulltext = compile(r'<div class="c2">.+?<strong>(.+?)<.+?', DOTALL)
		windSpeed = fulltext.findall(html)
		if DEBUG:
			FAlog("windSpeed=%s" % str(windSpeed))

		timeEntries = len(zeit)
		x = 0
		while x < timeEntries:
			# description[x] = self.konvert_uml(str(sub(r'<[^>]*>', "", description[x])))
			feels[x] = self.konvert_uml(str(sub(r'<[^>]*>', "", feels[x])))
			precip[x] = self.konvert_uml(str(sub(r'<[^>]*>', "", precip[x])))
			humidity[x] = self.konvert_uml(str(sub(r'<[^>]*>', "", humidity[x])))
			windSpeed[x] = self.filter_dia(windSpeed[x])

			# translate_description
			description[x] = self.konvert_uml(str(sub(r'<[^>]*>', "", description[x])))
			description[x] = self.translate_description(description[x], translation_dict)
			print("description[x]=", description[x])
			# translate_description end

			if DEBUG:
				FAlog("weather: %s, %s, %s, %s, %s, %s, %s, %s" % (zeit[x], temp[x], windDirection[x], windSpeed[x], description[x], feels[x], precip[x], humidity[x]))
			datalist.append([thumbnails[x], zeit[x], temp[x], windDirection[x], windSpeed[x], description[x], feels[x], precip[x], humidity[x]])
			x += 1

		# self["Titel2"].text = ""  # titel[0].strip("'")
		self["Titel2"].text = titel[0].strip("'")
		# translation date
		datum = titel[0]
		foundPos = datum.rfind(" ")
		foundPos2 = datum.find(" ")
		day_text = datum[:foundPos2].strip()
		month_text = datum[foundPos2:foundPos].strip()
		translated_day = translation_dict.get(day_text.lower(), day_text)
		translated_month = translation_dict.get(month_text.lower(), month_text)
		translated_day = translated_day.capitalize()
		translated_month = translated_month.capitalize()
		datum2 = translated_day + ", " + datum[foundPos:] + ". " + translated_month

		foundPos = self.ort.find("/")
		plaats = _(self.ort[0:foundPos]) + "-" + self.ort[foundPos + 1:len(self.ort)]
		self["Titel"].text = plaats.replace("_", " ") + "  -  " + datum2
		self["Titel4"].text = plaats.replace("_", " ")
		self["Titel5"].text = datum2
		self["Titel3"].text = self.ort[:foundPos].replace("_", " ") + "\r\n" + self.ort[foundPos + 1:].replace("_", " ") + "\r\n" + datum2
		self["MainList"].SetList(datalist)
		self["MainList"].selectionEnabled(0)
		self["MainList"].show
		# self.deactivateCacheDialog()

	def load_translation_dict(self, lng):
		dict_file = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/dict/%sdict.txt" % lng
		if not exists(dict_file):
			dict_file = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/dict/endict.txt"
		# print('dict_file=', dict_file)
		translation_dict = {}
		with open(dict_file, 'r') as file:
			for line in file:
				parts = line.strip().split('=')
				if len(parts) == 2:
					key, value = parts
					translation_dict[key.strip().lower()] = value.strip()
		return translation_dict

	def translate_description(self, description, translation_dict):
		cleaned_description = sub(r'[\t\r\n]', ' ', description).strip()
		if cleaned_description.lower() in translation_dict:
			return translation_dict[cleaned_description.lower()]
		words = cleaned_description.split()
		return ' '.join([translation_dict.get(word.lower(), word) for word in words])

	def filter_dia(self, text):
		filterItem = 0
		while filterItem < FILTERidx:
			text = text.replace(FILTERin[filterItem], FILTERout[filterItem])
			filterItem += 1
		return text

	def konvert_uml(self, text):
		text = self.filter_dia(text)
		return text[text.rfind("\\t") + 2:len(text)]


# ------------------------------------------------------------------------------------------
# ------------------------------ City Panel ------------------------------------------------
# ------------------------------------------------------------------------------------------


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
					<eLabel backgroundColor="red" cornerRadius="3" position="10,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="green" cornerRadius="3" position="305,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="yellow" cornerRadius="3" position="600,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="blue" cornerRadius="3" position="895,65" size="295,6" zPosition="11" />
					<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
					<eLabel backgroundColor="grey" position="10,80" size="1180,2" />
					<widget name="Mlist" itemHeight="35" position="10,90" size="1180,665" enableWrapAround="1" scrollbarMode="showOnDemand" />
					<eLabel backgroundColor="grey" position="10,770" size="1180,2" />
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
				<eLabel backgroundColor="red" cornerRadius="3" position="14,87" size="394,8" zPosition="11"/>
				<eLabel backgroundColor="green" cornerRadius="3" position="407,87" size="394,8" zPosition="11"/>
				<eLabel backgroundColor="yellow" cornerRadius="3" position="800,87" size="394,8" zPosition="11"/>
				<eLabel backgroundColor="blue" cornerRadius="3" position="1194,87" size="394,8" zPosition="11"/>
				<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#a08500" font="Regular;40" halign="center" position="800,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#18188b" font="Regular;40" halign="center" position="1194,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_blue" transparent="1" valign="center" zPosition="1"/>
				<eLabel backgroundColor="grey" position="14,107" size="1574,3"/>
				<widget name="Mlist" itemHeight="47" position="14,120" size="1574,887" enableWrapAround="1" scrollbarMode="showOnDemand"/>
				<eLabel backgroundColor="grey" position="14,1027" size="1574,3"/>
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
				<eLabel backgroundColor="red" cornerRadius="3" position="6,43" size="196,4" zPosition="11"/>
				<eLabel backgroundColor="green" cornerRadius="3" position="203,43" size="196,4" zPosition="11"/>
				<eLabel backgroundColor="yellow" cornerRadius="3" position="400,43" size="196,4" zPosition="11"/>
				<eLabel backgroundColor="blue" cornerRadius="3" position="596,43" size="196,4" zPosition="11"/>
				<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#a08500" font="Regular;20" halign="center" position="400,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
				<widget backgroundColor="#18188b" font="Regular;20" halign="center" position="596,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_blue" transparent="1" valign="center" zPosition="1"/>
				<eLabel backgroundColor="grey" position="6,53" size="786,1"/>
				<widget name="Mlist" itemHeight="23" position="6,60" size="786,443" enableWrapAround="1" scrollbarMode="showOnDemand"/>
				<eLabel backgroundColor="grey" position="6,513" size="786,1"/>
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

		# global city
		self.city = panelmenu
		# print('city = panelmenu:', self.city, type(self.city))
		self["key_green"] = StaticText(_("Favorite 1"))
		self["key_yellow"] = StaticText(_("Favorite 2"))
		self["key_blue"] = StaticText(_("Home"))
		self["key_ok"] = StaticText(_("Forecast"))
		self.setTitle(_("Select a city"))

		self.filtered_list = []
		self.search_text = ""
		global search_ok
		search_ok = False

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"text": (self.openKeyboard, _("Open Keyboard")),
				"cancel": (self.exit, _("Exit - End")),
				"red": (self.exit, _("Exit - End")),
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
			},
			-2
		)

		self.onShown.append(self.prepare)

	def openKeyboard(self):
		from Screens.VirtualKeyBoard import VirtualKeyBoard
		self.session.openWithCallback(
			self.filter,
			VirtualKeyBoard,
			title=_("Search your City"),
			text='Rome')

	def filter(self, result):
		if result:
			try:
				self.filtered_list = []
				search = result.lower()
				for item in self.Mlist:
					city_name = item[0][0]
					# print('city_name:', city_name)
					if search in city_name.lower():
						global search_ok
						search_ok = True
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
		global search_ok
		if search_ok is True:
			search_ok = False
			# self.prepare()
		# else:
		global menu
		menu = "stop"
		# print('self.city=:', self.city)
		self.close(self.city)

	def ok(self):
		selected_city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])  # Selezione dell'utente
		print("OK city= %s" % selected_city, "CurrentSelection= %s" % self['Mlist'].l.getCurrentSelection())
		if DEBUG:
			FAlog("city= %s" % selected_city, "CurrentSelection= %s" % self['Mlist'].l.getCurrentSelection())
		self.close(selected_city)  # Restituisci direttamente la stringa selezionata

	def blue(self):
		global start
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		if DEBUG:
			FAlog("Home:", self.city)
		config.plugins.foreca.home.setValue(self.city)  # ✅ FIX
		config.plugins.foreca.home.save()
		start = self.city[self.city.rfind("/") + 1:]
		message = "%s %s" % (_("This city is stored as home!\n\n                                  "), self.city)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=8)

	def green(self):
		global fav1
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		if DEBUG:
			FAlog("Fav1:", self.city)
		config.plugins.foreca.fav1.setValue = (self.city)
		config.plugins.foreca.fav1.save()
		fav1 = self.city[self.city.rfind("/") + 1:len(self.city)]  # ✅ FIX
		message = "%s %s" % (_("This city is stored as favorite 1!\n\n                             "), self.city)
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=8)

	def yellow(self):
		global fav2
		self.city = sub(r" ", "_", self['Mlist'].l.getCurrentSelection()[0][1])
		if DEBUG:
			FAlog("Fav2:", self.city)
		config.plugins.foreca.fav2.setValue = (self.city)  # ✅ FIX
		config.plugins.foreca.fav2.save()
		fav2 = self.city[self.city.rfind("/") + 1:len(self.city)]
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

# ------------------------------------------------------------------------------------------
# ------------------------------ Satellite photos ------------------------------------------
# ------------------------------------------------------------------------------------------


class SatPanelList(MenuList):

	if HD:
		ItemSkin = 143
	else:
		ItemSkin = 123

	def __init__(self, list, font0=28, font1=16, itemHeight=ItemSkin, enableWrapAround=True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		GUIComponent.__init__(self)
		self.font0 = gFont("Regular", font0)
		self.font1 = gFont("Regular", font1)
		self.itemHeight = itemHeight
		self.pictScale = 0
		self.foregroundColorSelected = 8900346
		self.foregroundColor = 0xffffff
		self.backgroundColorSelected = 0x565656
		self.textPos = 230, 45, 380, 50

# ---------------------- get skin attribs ----------------------------
	def applySkin(self, desktop, parent):

		def warningWrongSkinParameter(string, wanted, given):
			print("[ForecaPreview] wrong '%s' skin parameters. Must be %d arguments (%d given)" % (string, wanted, given))

		def font(value):
			self.font0 = parseFont(value, ((1, 1), (1, 1)))

		def font1(value):
			self.font1 = parseFont(value, ((1, 1), (1, 1)))

		def itemHeight(value):
			self.itemHeight = int(value)

		def setPictScale(value):
			self.pictScale = int(value)

		def foregroundColor(value):
			self.foregroundColor = parseColor(value).argb()

		def foregroundColorSelected(value):
			self.foregroundColorSelected = parseColor(value).argb()

		def backgroundColorSelected(value):
			self.backgroundColorSelected = parseColor(value).argb()

		def textPos(value):
			self.textPos = list(map(int, value.split(",")))
			lx = len(self.textPos)
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
		self.l.setItemHeight(self.itemHeight)
		return GUIComponent.applySkin(self, desktop, parent)


class SatPanel(Screen, HelpableScreen):

	def __init__(self, session, ort):
		self.session = session

		if size_w == 1920:
			self.skin = """
				<screen name="SatPanel" position="center,center" size="1200,900" title="Satellite photos" >
					<eLabel backgroundColor="red" cornerRadius="3" position="10,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="green" cornerRadius="3" position="305,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="yellow" cornerRadius="3" position="600,65" size="295,6" zPosition="11" />
					<eLabel backgroundColor="blue" cornerRadius="3" position="895,65" size="295,6" zPosition="11" />
					<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
					<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
					<eLabel backgroundColor="grey" position="10,80" size="1180,2" />
					<widget enableWrapAround="1" name="Mlist" itemHeight="145" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
					<eLabel backgroundColor="grey" position="10,770" size="1180,2" />
					<ePixmap position="1025,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png" />
					<ePixmap position="379,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png" />
					<ePixmap position="42,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" />
					<ePixmap position="705,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png" />
					<ePixmap position="1085,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png" />
				</screen>"""
		elif size_w == 2560:
			self.skin = """
				<screen name="SatPanel" position="center,center" size="1600,1200" title="Satellite photos">
					<eLabel backgroundColor="red" cornerRadius="3" position="14,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="green" cornerRadius="3" position="407,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="yellow" cornerRadius="3" position="800,87" size="394,8" zPosition="11"/>
					<eLabel backgroundColor="blue" cornerRadius="3" position="1194,87" size="394,8" zPosition="11"/>
					<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#a08500" font="Regular;40" halign="center" position="800,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#18188b" font="Regular;40" halign="center" position="1194,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="grey" position="14,107" size="1574,3"/>
					<widget enableWrapAround="1" name="Mlist" itemHeight="194" position="14,120" scrollbarMode="showOnDemand" size="1574,960"/>
					<eLabel backgroundColor="grey" position="14,1027" size="1574,3"/>
					<ePixmap position="1367,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
					<ePixmap position="506,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
					<ePixmap position="56,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="940,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
					<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="1447,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
				</screen>"""
		else:
			self.skin = """
				<screen name="SatPanel" position="center,center" size="800,600" title="Satellite photos">
					<eLabel backgroundColor="red" cornerRadius="3" position="6,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="green" cornerRadius="3" position="203,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="yellow" cornerRadius="3" position="400,43" size="196,4" zPosition="11"/>
					<eLabel backgroundColor="blue" cornerRadius="3" position="596,43" size="196,4" zPosition="11"/>
					<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#a08500" font="Regular;20" halign="center" position="400,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_yellow" transparent="1" valign="center" zPosition="1"/>
					<widget backgroundColor="#18188b" font="Regular;20" halign="center" position="596,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="grey" position="6,53" size="786,1"/>
					<widget enableWrapAround="1" name="Mlist" itemHeight="96" position="6,60" scrollbarMode="showOnDemand" size="786,480"/>
					<eLabel backgroundColor="grey" position="6,513" size="786,1"/>
					<ePixmap position="683,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_text.png"/>
					<ePixmap position="252,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_menu.png"/>
					<ePixmap position="28,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="470,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_info.png"/>
					<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="723,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
				</screen>"""

		Screen.__init__(self, session)
		self.setup_title = _("Satellite photos")
		self["Mlist"] = SatPanelList([])
		self.ort = ort
		self.loc_id = ''
		self["key_red"] = StaticText(_("Continents"))
		self["key_green"] = StaticText(_("Europe"))
		self["key_yellow"] = StaticText(_("Germany"))
		self["key_blue"] = StaticText(_("Settings"))
		self.setTitle(_("Satellite photos"))
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"cancel": (self.exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"red": (self.MapsContinents, _("Red - Continents")),
				"green": (self.MapsEurope, _("Green - Europe")),
				"yellow": (self.MapsGermany, _("Yellow - Germany")),
				"blue": (self.PicSetupMenu, _("Blue - Settings")),
				"ok": (self.ok, _("OK - Show")),
			},
			-2
		)
		self.onShown.append(self.prepare)

	def prepare(self):
		self.Mlist = []
		self.Mlist.append(self.SatEntryItem((_("Air pressure"), 'pressure')))
		self.Mlist.append(self.SatEntryItem((_("Cloudcover Video"), 'cloud')))
		self.Mlist.append(self.SatEntryItem((_("Showerradar Video"), 'rain')))
		self.Mlist.append(self.SatEntryItem((_("Temperature Video"), 'temp')))
		self.Mlist.append(self.SatEntryItem((_("Weather map Video"), 'sat')))
		self.Mlist.append(self.SatEntryItem((_("Eumetsat"), 'eumetsat')))

		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)

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

	def exit(self):
		global menu
		menu = "stop"
		self.close()

	def deactivateCacheDialog(self):
		self.cacheDialog.stop()
		self.working = False

	def ok(self):
		menu = self['Mlist'].l.getCurrentSelection()[0][1]
		if DEBUG:
			FAlog("SatPanel menu= %s" % menu, "CurrentSelection= %s" % self['Mlist'].l.getCurrentSelection())

		self.cacheDialog = self.session.instantiateDialog(ForecaPreviewCache)
		self.cacheDialog.start()
		self.SatBild()

	def MapsGermany(self):
		itemList = [
			(_("Baden-Wuerttemberg"), 'badenwuerttemberg'),
			(_("Bavaria"), 'bayern'),
			(_("Berlin"), 'berlin'),
			(_("Brandenburg"), 'brandenburg'),
			(_("Bremen"), 'bremen'),
			(_("Hamburg"), 'hamburg'),
			(_("Hesse"), 'hessen'),
			(_("Lower Saxony"), 'niedersachsen'),
			(_("Mecklenburg-Vorpommern"), 'mecklenburgvorpommern'),
			(_("North Rhine-Westphalia"), 'nordrheinwestfalen'),
			(_("Rhineland-Palatine"), 'rheinlandpfalz'),
			(_("Saarland"), 'saarland'),
			(_("Saxony"), 'sachsen'),
			(_("Saxony-Anhalt"), 'sachsenanhalt'),
			(_("Schleswig-Holstein"), 'schleswigholstein'),
			(_("Thuringia"), 'thueringen'),
		]
		itemList.sort(key=lambda i: strxfrm(i[0]))
		self.Mlist = []
		for item in itemList:
			self.Mlist.append(self.SatEntryItem(item))
		self.session.open(SatPanelb, self.ort, _("Germany"), self.Mlist)

	def MapsEurope(self):
		itemList = [
			(_("Austria"), 'oesterreich'),
			(_("Belgium"), 'belgien'),
			(_("Czech Republic"), 'tschechien'),
			(_("Denmark"), 'daenemark'),
			(_("France"), 'frankreich'),
			(_("Germany"), 'deutschland'),
			(_("Greece"), 'griechenland'),
			(_("Great Britain"), 'grossbritannien'),
			(_("Hungary"), 'ungarn'),
			(_("Ireland"), 'irland'),
			(_("Italy"), 'italien'),
			(_("Latvia"), 'lettland'),
			(_("Luxembourg"), 'luxemburg'),
			(_("Netherlands"), 'niederlande'),
			(_("Poland"), 'polen'),
			(_("Portugal"), 'portugal'),
			(_("Russia"), 'russland'),
			(_("Slovakia"), 'slowakei'),
			(_("Spain"), 'spanien'),
			(_("Switzerland"), 'schweiz'),
		]
		itemList.sort(key=lambda i: strxfrm(i[0]))
		self.Mlist = []
		for item in itemList:
			self.Mlist.append(self.SatEntryItem(item))
		self.session.open(SatPanelb, self.ort, _("Europe"), self.Mlist)

	def MapsContinents(self):
		self.Mlist = []
		self.Mlist.append(self.SatEntryItem((_("Europe"), 'europa')))
		self.Mlist.append(self.SatEntryItem((_("Middle East"), 'naherosten')))
		self.Mlist.append(self.SatEntryItem((_("North Africa"), 'afrika_nord')))
		self.Mlist.append(self.SatEntryItem((_("South Africa"), 'afrika_sued')))
		self.Mlist.append(self.SatEntryItem((_("North America"), 'nordamerika')))
		self.Mlist.append(self.SatEntryItem((_("Middle America"), 'mittelamerika')))
		self.Mlist.append(self.SatEntryItem((_("South America"), 'suedamerika')))
		self.Mlist.append(self.SatEntryItem((_("East Asia"), 'ostasien')))
		self.Mlist.append(self.SatEntryItem((_("Middle Asia"), 'zentralasien')))
		self.Mlist.append(self.SatEntryItem((_("Southeast Asia"), 'suedostasien')))
		self.Mlist.append(self.SatEntryItem((_("Australia"), 'australienundozeanien')))
		self.session.open(SatPanelb, self.ort, _("Continents"), self.Mlist)

# ------------------------------------------------------------------------------------------

	def SatEntryItem(self, entry):
		pict_scale = self["Mlist"].pictScale
		ItemSkin = self["Mlist"].itemHeight
		mblau = self["Mlist"].foregroundColorSelected
		weiss = self["Mlist"].foregroundColor
		grau = self["Mlist"].backgroundColorSelected

		res = [entry]
		if DEBUG:
			FAlog("entry=", entry)
		thumb = LoadPixmap(THUMB_PATH + entry[1] + ".png")
		thumb_width = 200
		if pict_scale:
			thumb_width = thumb.size().width()
		res.append(MultiContentEntryPixmapAlphaTest(pos=(2, 2), size=(thumb_width, ItemSkin - 4), png=thumb))  # png vorn
		x, y, w, h = self["Mlist"].textPos
		res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=0, text=entry[0], color=weiss, color_sel=mblau, backcolor_sel=grau, flags=RT_VALIGN_CENTER))
		return res

# ------------------------------------------------------------------------------------------

	def PicSetupMenu(self):
		self.session.openWithCallback(self.OKCallback, PicSetup)

	def OKCallback(self, callback=None):
		global fav1, fav2, start
		fav1 = str(config.plugins.foreca.fav1.value)
		fav2 = str(config.plugins.foreca.fav2.value)
		start = str(config.plugins.foreca.home.value)
		city = start
		self.ort = city
		self.exit()

	def fetch_url(self, x):
		menu = self['Mlist'].l.getCurrentSelection()[0][1]
		if not x.startswith("http"):
			x = "https:" + x
		url = x
		if '[TYPE]' in url:
			url = url.replace('[TYPE]', menu)

		global foundz
		foundz = 'jpg'
		foundPos = url.find("0000.jpg")
		if DEBUG:
			FAlog("x= {}".format(x), "url= {}, foundPos= {}".format(url, foundPos))
		if foundPos == -1:
			foundPos = url.find(".jpg")
		if foundPos == -1:
			foundPos = url.find(".png")
			foundz = 'png'
		file = url[foundPos - 10:foundPos]
		file2 = file[0:4] + "-" + file[4:6] + "-" + file[6:8] + " - " + file[8:10] + " " + _("h")
		file2 = file2.replace(" ", "")
		if DEBUG:
			FAlog("file= %s file2= %s" % (file, file2))
		req = Request(url, headers=HEADERS)
		resp = urlopen(req, timeout=10)
		with open("%s%s.%s" % (CACHE_PATH, file2, foundz), 'wb') as f:
			f.write(resp.read())

	def doContext(self):
		text = _("Select action")
		base_url = "https://www.sat24.com"

		try:
			response = requests.get(base_url + "/en-gb/continent/eu", headers=HEADERS, timeout=10)
			response.raise_for_status()
			html = response.text if PY3 else response.content
		except requests.RequestException as e:
			print("Error while page download: %s" % str(e))
			return
		pattern = r'<li class=".*?">\s*<a .*?href="([^"]+)".*?>\s*(.*?)\s*</a>'
		matches = findall(pattern, html)
		seen_links = set()
		menu = []

		for href, title in matches:
			if 'satellite' in title.lower():
				link = base_url + href
				if link not in seen_links:
					menu.append((title.strip(), link))
					seen_links.add(link)

		def returnToChoiceBox(result=None):
			self.session.openWithCallback(boxAction, ChoiceBox, title=text, list=menu)

		def boxAction(choice):
			if choice:
				title, url = choice
				devicepath = join(CACHE_PATH, "meteogram.png")
				try:
					req = Request(url, headers=HEADERS)
					resp = urlopen(req, timeout=10)
					content = resp.read().decode('utf-8') if PY3 else resp.read()
					pattern = r'<div class="absolute w-full h-full overflow-hidden z-10">.*?<img .*?alt="satLayer".*?src="([^"]+)".*?>'
					matches = findall(pattern, content, DOTALL)
					if matches:
						chosen_link = matches[0]
						# print("Link select:", chosen_link)
						if not chosen_link.startswith("http"):
							chosen_link = base_url + chosen_link
						try:
							img_response = requests.get(chosen_link, headers=HEADERS, timeout=10)
							img = Image.open(BytesIO(img_response.content))
							img = img.convert("RGB")  # Rimuove ICC
							img.save(devicepath, "PNG")
							if DEBUG:
								FAlog("Image dimensions: {}x{}".format(img.width, img.height))
							self.session.openWithCallback(returnToChoiceBox, PicView, devicepath, 0, False)
						except requests.RequestException as e:
							if DEBUG:
								FAlog("Error downloading image: %s" % str(e))
							returnToChoiceBox()
					else:
						if DEBUG:
							FAlog("Image not found on the page.")
						returnToChoiceBox()
				except Exception as e:
					if DEBUG:
						FAlog("Error processing page: %s" % str(e))
					returnToChoiceBox()

		if len(menu) > 0:
			self.session.openWithCallback(boxAction, ChoiceBox, title=text, list=menu)

	def SatBild(self):
		try:
			current_selection = self['Mlist'].l.getCurrentSelection()
			if not current_selection or not current_selection[0] or len(current_selection[0]) < 2:
				if DEBUG:
					FAlog("SatBild Error: Invalid selection in CurrentSelection", str(current_selection))
				return
			menu = current_selection[0][1]
			if DEBUG:
				FAlog("SatBild menu= %s" % menu, "CurrentSelection= %s" % current_selection)
			self.deactivateCacheDialog()
			if menu == "eumetsat":
				self.doContext()
			else:
				try:
					url = "%s%s?map=%s" % (BASEURL, pathname2url(self.ort), menu)
					if DEBUG:
						FAlog("VIDEO URL map = %s" % url)
					req = Request(url, headers=HEADERS)
					resp = urlopen(req, timeout=10)
					content = (resp.read().decode('utf-8') if PY3 else resp.read())
					start_pattern = r"var urltemplate"
					end_pattern = r"var timehdrs"
					section_pattern = compile(r"%s(.*?)%s" % (start_pattern, end_pattern), DOTALL)
					section_match = section_pattern.search(content)

					if section_match:
						section_content = section_match.group(1)
						fulltext = compile(r'(\/\/cache.*?\.(jpg|png))', DOTALL)
						urls = fulltext.findall(section_content)
						for url, ext in urls:
							full_url = 'https:' + url
							if DEBUG:
								FAlog("Valid URL:", full_url)
							self.fetch_url(full_url)
						self.session.open(View_Slideshow, 0, True)
					else:
						if DEBUG:
							FAlog("SatBild Warning: No image URLs found in page content.")
						self.session.open(MessageBox, _("No satellite images found."), MessageBox.TYPE_INFO)
						return
				except Exception as e:
					self.session.open(MessageBox, _("Failed to process satellite data: %s" % str(e)), MessageBox.TYPE_ERROR)
		except Exception as e:
			if DEBUG:
				FAlog("SatBild Critical Error", str(e))
			self.session.open(MessageBox, _("A critical error occurred: %s" % str(e)), MessageBox.TYPE_ERROR)


# ------------------------------------------------------------------------------------------
# ------------------------------ Weather Maps ----------------------------------------------
# ------------------------------------------------------------------------------------------


class SatPanelListb(MenuList):

	if HD:
		ItemSkin = 143
	else:
		ItemSkin = 123

	def __init__(self, list, font0=24, font1=16, itemHeight=ItemSkin, enableWrapAround=True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.font0 = gFont("Regular", font0)
		self.font1 = gFont("Regular", font1)
		self.itemHeight = itemHeight

# ---------------------- get skin attribs ----------------------------
	def applySkin(self, desktop, parent):
		def font(value):
			self.font0 = parseFont(value, ((1, 1), (1, 1)))

		def font1(value):
			self.font1 = parseFont(value, ((1, 1), (1, 1)))

		def itemHeight(value):
			self.itemHeight = int(value)

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


class SatPanelb(Screen, HelpableScreen):

	def __init__(self, session, ort, title, mlist):
		self.session = session
		self.ort = ort

		if size_w == 1920:
			self.skin = """
				<screen name="SatPanelb" position="center,center" size="1200,900">
					<eLabel backgroundColor="blue" cornerRadius="3" position="895,65" size="295,6" zPosition="11" />
					<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
					<eLabel backgroundColor="grey" position="10,80" size="1180,2" />
					<widget name="Mlist" enableWrapAround="1" itemHeight="144" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
					<eLabel backgroundColor="grey" position="10,770" size="1180,2" />
					<ePixmap position="42,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" />
					<ePixmap position="1135,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png" />
					<ePixmap position="1085,864" size="60,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png" />
				</screen>
			"""
		elif size_w == 2560:
			self.skin = """
				<screen name="SatPanelb" position="center,center" size="1600,1200">
					<eLabel backgroundColor="blue" cornerRadius="3" position="1194,87" size="394,8" zPosition="11"/>
					<widget backgroundColor="#18188b" font="Regular;40" halign="center" position="1194,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="grey" position="14,107" size="1574,3"/>
					<widget name="Mlist" enableWrapAround="1" itemHeight="192" position="14,120" scrollbarMode="showOnDemand" size="1574,960"/>
					<eLabel backgroundColor="grey" position="14,1027" size="1574,3"/>
					<ePixmap position="56,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="1514,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="1447,1152" size="80,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
				</screen>
			"""
		else:
			self.skin = """
				<screen name="SatPanelb" position="center,center" size="800,600">
					<eLabel backgroundColor="blue" cornerRadius="3" position="596,43" size="196,4" zPosition="11"/>
					<widget backgroundColor="#18188b" font="Regular;20" halign="center" position="596,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_blue" transparent="1" valign="center" zPosition="1"/>
					<eLabel backgroundColor="grey" position="6,53" size="786,1"/>
					<widget name="Mlist" enableWrapAround="1" itemHeight="96" position="6,60" scrollbarMode="showOnDemand" size="786,480"/>
					<eLabel backgroundColor="grey" position="6,513" size="786,1"/>
					<ePixmap position="28,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png"/>
					<ePixmap position="756,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_next.png"/>
					<ePixmap position="723,576" size="40,20" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_prev.png"/>
				</screen>
			"""

		Screen.__init__(self, session)
		self.setup_title = title
		self.Mlist = mlist
		if DEBUG:
			FAlog("Mlist= %s" % self.Mlist, "\nSatPanelListb([])= %s" % SatPanelListb([]))
		self["Mlist"] = SatPanelListb([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_blue"] = StaticText(_("Settings"))
		self.setTitle(title)
		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(
			self, "ForecaActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"blue": (self.PicSetupMenu, _("Blue - Settings")),
				"ok": (self.ok, _("OK - Show")),
			},
			-2,
		)

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

	def Exit(self):
		global menu
		menu = "stop"
		self.close()

	def ok(self):
		menu = self['Mlist'].l.getCurrentSelection()[0][1]
		if DEBUG:
			FAlog("SatPanelb menu= %s" % menu, "CurrentSelection= %s" % self['Mlist'].l.getCurrentSelection())
		self.SatBild()

	def PicSetupMenu(self):
		self.session.openWithCallback(self.OKCallback, PicSetup)

	def OKCallback(self, callback=None):
		global fav1, fav2, start
		# self.ort = city
		fav1 = str(config.plugins.foreca.fav1.value)
		fav2 = str(config.plugins.foreca.fav2.value)
		start = str(config.plugins.foreca.home.value)
		self.ort = start
		self.Exit()

	def SatBild(self):
		try:
			current_selection = self['Mlist'].l.getCurrentSelection()
			if not current_selection or not current_selection[0] or len(current_selection[0]) < 2:
				if DEBUG:
					FAlog("SatBild Error: Invalid selection in CurrentSelection", str(current_selection))
				self.session.open(MessageBox, _("Invalid selection. Please select a valid region."), MessageBox.TYPE_ERROR)
				return

			region = current_selection[0][1]
			if DEBUG:
				FAlog("SatBild: Selected region = %s" % region)
			devicepath = CACHE_PATH + "meteogram.png"
			url = "http://img.wetterkontor.de/karten/" + region + "0.jpg"
			if DEBUG:
				FAlog("SatBild: Downloading image from URL = %s" % url)

			try:
				download_image(url, devicepath)
				remove_icc_profile(devicepath)
				"""
				req = Request(url, headers=HEADERS)
				resp = urlopen(req, timeout=2)
				with open(devicepath, 'wb') as f:
					f.write(resp.read())
					img = Image.open(devicepath)
					img.save(devicepath, icc_profile=None)
				"""
				self.session.open(PicView, devicepath, 0, False)
			except Exception as e:
				if DEBUG:
					FAlog("SatBild Error: Failed to download or save the image", str(e))
				self.session.open(MessageBox, _("Failed to load the satellite image: %s" % str(e)), MessageBox.TYPE_ERROR)

		except Exception as e:
			if DEBUG:
				FAlog("SatBild Critical Error", str(e))
			self.session.open(MessageBox, _("A critical error occurred: %s" % str(e)), MessageBox.TYPE_ERROR)


# ------------------------------------------------------------------------------------------
# -------------------------- Picture viewer for large pictures -----------------------------
# ------------------------------------------------------------------------------------------


class PicView(Screen):

	def __init__(self, session, filelist, index, startslide):
		self.session = session
		self.bgcolor = config.plugins.foreca.bgcolor.value
		space = config.plugins.foreca.framesize.value

		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" > \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.bgcolor + "\" /> \
			<widget name=\"pic\" position=\"" + str(space) + "," + str(space) + "\" size=\"" + str(size_w - (space * 2)) + "," + str(size_h - (space * 2)) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			</screen>"

		Screen.__init__(self, session)
		self["actions"] = ActionMap(
			["OkCancelActions", "MediaPlayerActions"],
			{
				"cancel": self.Exit,
				"stop": self.Exit,
			},
			-1
		)

		self["pic"] = Pixmap()
		self.filelist = filelist
		self.old_index = 0
		self.lastindex = index
		self.currPic = []
		self.shownow = True
		self.dirlistcount = 0
		self.index = 0
		self.picload = ePicLoad()
		# self.picload.PictureData.get().append(self.finish_decode)
		try:
			self.picload.PictureData.get().append(self.finish_decode)
		except:
			self.picload_conn = self.picload.PictureData.connect(self.finish_decode)
		self.onLayoutFinish.append(self.setPicloadConf)

		self.startslide = startslide

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
				# remove_icc_profile(self.currPic[0])
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

# ------------------------------------------------------------------------------------------
# ------------------------------ Slide Show ------------------------------------------------
# ------------------------------------------------------------------------------------------


class View_Slideshow(Screen):

	def __init__(self, session, pindex=0, startslide=False):

		if DEBUG:
			FAlog("SlideShow is running...")
		self.textcolor = config.plugins.foreca.textcolor.value
		self.bgcolor = config.plugins.foreca.bgcolor.value
		space = config.plugins.foreca.framesize.value
		fontsize = config.plugins.foreca.fontsize.value

		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.bgcolor + "\" /> \
			<widget name=\"pic\" position=\"" + str(space) + "," + str(space + 40) + "\" size=\"" + str(size_w - (space * 2)) + "," + str(size_h - (space * 2) - 40) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget name=\"point\" position=\"" + str(space + 5) + "," + str(space + 10) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"" + THUMB_PATH + "record.png\" alphatest=\"on\" /> \
			<widget name=\"play_icon\" position=\"" + str(space + 25) + "," + str(space + 10) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"" + THUMB_PATH + "ico_mp_play.png\"  alphatest=\"on\" /> \
			<widget name=\"file\" position=\"" + str(space + 45) + "," + str(space + 10) + "\" size=\"" + str(size_w - (space * 2) - 50) + "," + str(fontsize + 5) + "\" font=\"Regular;" + str(fontsize) + "\" halign=\"left\" foregroundColor=\"" + self.textcolor + "\" zPosition=\"2\" noWrap=\"1\" transparent=\"1\" /> \
			</screen>"
		Screen.__init__(self, session)

		self["actions"] = ActionMap(
			["OkCancelActions", "MediaPlayerActions"],
			{
				"cancel": self.Exit,
				"stop": self.Exit,
				"pause": self.PlayPause,
				"play": self.PlayPause,
				"previous": self.prevPic,
				"next": self.nextPic,
			},
			-1
		)

		self["point"] = Pixmap()
		self["pic"] = Pixmap()
		self["play_icon"] = Pixmap()
		self["file"] = Label(_("Please wait, photo is being loaded ..."))
		self.old_index = 0
		self.picfilelist = []
		self.lastindex = pindex
		self.currPic = []
		self.shownow = True
		self.dirlistcount = 0

		self.filelist = FileList(CACHE_PATH, showDirectories=False, matchingPattern=r"^.*\.(jpg|png)$", useServiceRef=False)
		for x in self.filelist.getFileList():
			if x[0][0]:
				if x[0][1] is False:
					self.picfilelist.append(x[0][0] if PY3 else CACHE_PATH + x[0][0])
				else:
					self.dirlistcount += 1

		self.maxentry = len(self.picfilelist) - 1
		self.pindex = pindex - self.dirlistcount
		if self.pindex < 0:
			self.pindex = 0

		self.picload = ePicLoad()
		# self.picload.PictureData.get().append(self.finish_decode)
		try:
			self.picload.PictureData.get().append(self.finish_decode)
		except:
			self.picload_conn = self.picload.PictureData.connect(self.finish_decode)

		self.slideTimer = eTimer()
		# self.slideTimer.callback.append(self.slidePic)
		try:
			self.slideTimer.callback.append(self.slidePic)
		except:
			self.slideTimer_conn = self.slideTimer.timeout.connect(self.slidePic)

		if self.maxentry >= 0:
			self.onLayoutFinish.append(self.setPicloadConf)
		if startslide is True:
			self.PlayPause()

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
		if "play_icon" in self and self["play_icon"]:
			self["play_icon"].hide()
		if "file" in self and self["file"] and config.plugins.foreca.infoline.value is False:
			self["file"].hide()
		self.start_decode()

	def ShowPicture(self):
		if self.shownow and len(self.currPic):
			self.shownow = False
			self["file"].setText(self.currPic[0].replace(".jpg", "").replace(".png", ""))
			self.lastindex = self.currPic[1]
			if self.currPic[2]:
				self["pic"].instance.setPixmap(self.currPic[2].__deref__())
			else:
				print("[ShowPicture] No image data present.")
			self.currPic = []
			self.nextDay()
			self.start_decode()

	def finish_decode(self, picInfo=""):
		self["point"].hide()
		ptr = self.picload.getData()
		if ptr is not None:
			text = ""
			# print("[finish_decode] Image data loaded successfully.")
			try:
				if picInfo:
					parts = picInfo.split('\n', 1)
					if parts and '/' in parts[0]:
						filename = parts[0].split('/')[-1]
						text = "(" + str(self.pindex + 1) + "/" + str(self.maxentry + 1) + ") " + filename
				self.currPic = [text, self.pindex, ptr]
				self.ShowPicture()
			except Exception as e:
				print("[finish_decode] Errore:", str(e))
		else:
			print("[finish_decode] No image data obtained from picload.")

	def start_decode(self):
		if self.pindex < 0 or self.pindex >= len(self.picfilelist):
			print("[start_decode] Index out of bounds: %d" % self.pindex)
			return

		filepath = self.picfilelist[self.pindex]
		if CACHE_PATH not in filepath:
			filepath = CACHE_PATH + filepath
		# print("[start_decode] filepath:", filepath)
		if not exists(filepath):
			# print("[start_decode] File not found: %s" % filepath)
			return

		try:
			self.picload.startDecode(filepath)
		except Exception as e:
			print("[start_decode] Error while decoding image: %s" % str(e))
		self["point"].show()

	def nextDay(self):
		self.pindex += 1
		if self.pindex > self.maxentry:
			self.pindex = 0

	def prev(self):
		self.pindex -= 1
		if self.pindex < 0:
			self.pindex = self.maxentry

	def slidePic(self):
		if DEBUG:
			FAlog("slide to next Picture index=" + str(self.lastindex))
		if config.plugins.foreca.loop.value is False and self.lastindex == self.maxentry:
			self.PlayPause()
		self.shownow = True
		self.ShowPicture()

	def PlayPause(self):
		if self.slideTimer.isActive():
			self.slideTimer.stop()
			self["play_icon"].hide()
		else:
			self.slideTimer.start(config.plugins.foreca.slidetime.value * 1000)
			self["play_icon"].show()
			self.nextPic()

	def prevPic(self):
		self.currPic = []
		self.pindex = self.lastindex
		self.prev()
		self.start_decode()
		self.shownow = True

	def nextPic(self):
		self.shownow = True
		self.ShowPicture()

	def clear_images(self):
		try:
			for filepath in self.picfilelist:
				full_path = join(CACHE_PATH, filepath)
				if exists(full_path):
					try:
						remove(full_path)
						# print("Image file removed:", full_path)
					except OSError as e:
						print("Error while removing file:", full_path, e)

			self.picfilelist = []

			if exists(CACHE_PATH):
				for filename in listdir(CACHE_PATH):
					if filename.endswith(".jpg") or filename.endswith(".png"):
						file_path = join(CACHE_PATH, filename)
						try:
							remove(file_path)
							# print("Image file removed:", file_path)
						except OSError as e:
							print("Error while removing file:", file_path, e)
		except Exception as e:
			print("Error no file:", e)

	def Exit(self):
		del self.picload
		self.clear_images()
		self.close(self.lastindex + self.dirlistcount)


# ------------------------------------------------------------------------------------------
# -------------------------------- Foreca Settings -----------------------------------------
# ------------------------------------------------------------------------------------------

class PicSetup(Screen, ConfigListScreen):

	if size_w == 1920:
		skin = """
		<screen name="PicSetup" position="center,center" size="1200,900" title="Setup">
			<eLabel backgroundColor="red" cornerRadius="3" position="10,65" size="295,6" zPosition="11" />
			<eLabel backgroundColor="green" cornerRadius="3" position="305,65" size="295,6" zPosition="11" />
			<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
			<eLabel backgroundColor="grey" position="10,80" size="1180,2" />
			<widget enableWrapAround="1" name="Mlist" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
			<eLabel backgroundColor="grey" position="10,770" size="1180,2" />
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
			<eLabel backgroundColor="red" cornerRadius="3" position="14,87" size="394,8" zPosition="11"/>
			<eLabel backgroundColor="green" cornerRadius="3" position="407,87" size="394,8" zPosition="11"/>
			<widget backgroundColor="#9f1313" font="Regular;40" halign="center" position="14,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_red" transparent="1" valign="center" zPosition="1"/>
			<widget backgroundColor="#1f771f" font="Regular;40" halign="center" position="407,7" render="Label" shadowColor="black" shadowOffset="-2,-2" size="394,94" source="key_green" transparent="1" valign="center" zPosition="1"/>
			<eLabel backgroundColor="grey" position="14,107" size="1574,3"/>
			<widget enableWrapAround="1" name="Mlist" position="14,120" scrollbarMode="showOnDemand" size="1574,960"/>
			<eLabel backgroundColor="grey" position="14,1027" size="1574,3"/>
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
			<eLabel backgroundColor="red" cornerRadius="3" position="6,43" size="196,4" zPosition="11"/>
			<eLabel backgroundColor="green" cornerRadius="3" position="203,43" size="196,4" zPosition="11"/>
			<widget backgroundColor="#9f1313" font="Regular;20" halign="center" position="6,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_red" transparent="1" valign="center" zPosition="1"/>
			<widget backgroundColor="#1f771f" font="Regular;20" halign="center" position="203,3" render="Label" shadowColor="black" shadowOffset="-2,-2" size="196,46" source="key_green" transparent="1" valign="center" zPosition="1"/>
			<eLabel backgroundColor="grey" position="6,53" size="786,1"/>
			<widget enableWrapAround="1" name="Mlist" position="6,60" scrollbarMode="showOnDemand" size="786,480"/>
			<eLabel backgroundColor="grey" position="6,513" size="786,1"/>
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
		self["actions"] = NumberActionMap(
			["SetupActions", "ColorActions", 'WizardActions'],
			{
				"ok": self.OKcity,
				"save": self.save,
				"green": self.save,
				"cancel": self.cancel,
				"red": self.cancel,
				"left": self.keyLeft,
				"right": self.keyRight,
				"up": self.keyUp,
				"down": self.keyDown,
				"0": self.keyNumber,
				"1": self.keyNumber,
				"2": self.keyNumber,
				"3": self.keyNumber,
				"4": self.keyNumber,
				"5": self.keyNumber,
				"6": self.keyNumber,
				"7": self.keyNumber,
				"8": self.keyNumber,
				"9": self.keyNumber,
			},
			-3,
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
		# self.list.append(getConfigListEntry(_("Type Server"), config.plugins.foreca.languages))
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
		# panelmenu = ""
		current_item = str(self["Mlist"].getCurrent()[1].getText())
		self.config_entry = None
		print("current_item:", type(current_item), current_item)
		print("config.plugins.foreca.home:", type(config.plugins.foreca.home), config.plugins.foreca.home.value)
		print("config.plugins.foreca.fav1:", type(config.plugins.foreca.fav1), config.plugins.foreca.fav1.value)
		print("config.plugins.foreca.fav2:", type(config.plugins.foreca.fav2), config.plugins.foreca.fav2.value)
		if current_item == config.plugins.foreca.home.value:
			self.config_entry = config.plugins.foreca.home
		elif current_item == config.plugins.foreca.fav1.value:
			self.config_entry = config.plugins.foreca.fav1
		elif current_item == config.plugins.foreca.fav2.value:
			self.config_entry = config.plugins.foreca.fav2

		print("Config entry actual:", self.config_entry.value)
		self.session.openWithCallback(self.OKCallback, CityPanel, self.config_entry)

	def OKCallback(self, city=None):
		print("Received city:", city)
		print("Type of self.config_entry before setValue:", self.config_entry, type(self.config_entry))

		if isinstance(city, ConfigText):
			city = city.getValue()
			print("Extracted city value:", city)

		city_parts = city.split("/")  # Separiamo il paese dalla città
		if len(city_parts) == 2:
			country, city_name = city_parts
			print("Country:", country)
			print("City:", city_name)
		else:
			print("ERROR: city format is incorrect")

		if not isinstance(city, str):
			print("ERROR: city is not a string! Current type:", type(city))
			return

		if not isinstance(self.config_entry, ConfigText):
			print("ERROR: self.config_entry is not a ConfigText instance! Current type:", type(self.config_entry))
			return

		if city is None:
			print("No city selected, exiting callback.")
			return

		self.config_entry.setValue(city)  # Ora dovrebbe essere sicuro
		self.config_entry.save()
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
		self.cancel()

	def cancel(self):
		for x in self["Mlist"].list:
			x[1].cancel()
		global menu
		menu = "stop"
		self.close()
		# self.close(False, self.session)

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

	def keyNumber(self, number):
		self["Mlist"].handleKey(KEY_0 + number)
		self.createSetup()

	def refreshPlugins(self):
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
