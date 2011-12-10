# -*- coding: UTF-8 -*-
#-------------------------------------------------------
#
#              Foreca Weatherprognosis
#
#   This Plugin retrieves the actual weather prediction
#   for the next 10 days from the Foreca website.
#
#        We wish all users wonderful weather!
#
#                 Version 2.4 Int
#
#                    28.11.2011
#
#     Source of information: http://www.foreca.com
#
#             Design and idea by
#                  @Bauernbub
#            enigma2 mod by mogli123
#
#-------------------------------------------------------

from Components.ActionMap import HelpableActionMap
from Components.ActionMap import ActionMap, NumberActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Language import language
from Components.Button import Button
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from os import environ
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.Console import Console
from Components.config import *
from Components.ConfigList import ConfigList, ConfigListScreen
from enigma import eListboxPythonMultiContent, ePicLoad, eServiceReference, eTimer, getDesktop, gFont, RT_HALIGN_LEFT
from os import listdir, popen
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.FileList import FileList
from time import sleep
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, fileExists
from Tools.HardwareInfo import HardwareInfo
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage

import htmlentitydefs, re, urllib2, urllib
from re import sub, split, search, match, findall
import os
from os import system, remove, path, walk, makedirs, listdir
from time import *
import string
import gettext

def localeInit():
	lang = language.getLanguage()
	environ["LANGUAGE"] = lang[:2]
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain("Foreca", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/Foreca/locale/"))

def _(txt):
	t = gettext.dgettext("Foreca", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

config.plugins.foreca = ConfigSubsection()
config.plugins.foreca.Device = ConfigSelection(default=resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/bilder/", choices = [(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/", _("...Plugins/Extensions/Foreca/")), ("/media/hdd/Foreca/", _("/media/hdd/Foreca/")), ("/var/swap/Foreca/", _("/var/swap/Foreca/"))])
config.plugins.foreca.resize = ConfigSelection(default="0", choices = [("0", _("simple")), ("1", _("better"))])
config.plugins.foreca.bgcolor = ConfigSelection(default="#00000000", choices = [("#00000000", _("black")),("#009eb9ff", _("blue")),("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.foreca.textcolor = ConfigSelection(default="#0038FF48", choices = [("#00000000", _("black")),("#009eb9ff", _("blue")),("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.foreca.framesize = ConfigInteger(default=5, limits=(5, 99))
config.plugins.foreca.remove = ConfigSelection(default="0", choices = [("0", _("Yes")), ("1", _("No"))])
config.plugins.foreca.slidetime = ConfigInteger(default=1, limits=(1, 60))
config.plugins.foreca.infoline = ConfigEnableDisable(default=True)
config.plugins.foreca.loop = ConfigEnableDisable(default=False)
config.plugins.foreca.citylabels = ConfigEnableDisable(default=False)

global PluginVersion
PluginVersion = "2.4 - 28-11-2011"

global MAIN_PAGE
MAIN_PAGE = _("http://www.foreca.com")
PNG_PATH = resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/picon/"
USR_PATH = "/etc/enigma2/Foreca"
deviceName = HardwareInfo().get_device_name()

# Make Path for Slideshow
if os.path.exists(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/bilder") is False:
	try:
		os.makedirs(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/bilder", 755)
	except:
		pass
# Make Path for user settings
if os.path.exists(USR_PATH) is False:
	try:
		os.makedirs(USR_PATH, 755)
	except:
		pass

#---------------------- Skin Functions ----------------------------------------------------
def getAspect():
	val = AVSwitch().getAspectRatioSetting()
	return val/2

def getScale():
	return AVSwitch().getFramebufferScale()

#------------------------------------------------------------------------------------------
#---------------------- class InfoBarAspectSelection --------------------------------------
#------------------------------------------------------------------------------------------

class InfoBarAspectSelection:
	STATE_HIDDEN = 0
	STATE_ASPECT = 1
	STATE_RESOLUTION = 2
	def __init__(self):
		self["AspectSelectionAction"] = HelpableActionMap(self, "InfobarAspectSelectionActions",
			{
				"aspectSelection": (self.ExGreen_toggleGreen, _("Aspect list...")),
			})
		self.__ExGreen_state = self.STATE_HIDDEN

	def ExGreen_doAspect(self):
		self.__ExGreen_state = self.STATE_ASPECT
		self.aspectSelection()

	def ExGreen_doResolution(self):
		self.__ExGreen_state = self.STATE_RESOLUTION
		self.resolutionSelection()

	def ExGreen_doHide(self):
		self.__ExGreen_state = self.STATE_HIDDEN

	def ExGreen_toggleGreen(self, arg=""):
		print self.__ExGreen_state
		if self.__ExGreen_state == self.STATE_HIDDEN:
			print "self.STATE_HIDDEN"
			self.ExGreen_doAspect()
		elif self.__ExGreen_state == self.STATE_ASPECT:
			print "self.STATE_ASPECT"
			self.ExGreen_doResolution()
		elif self.__ExGreen_state == self.STATE_RESOLUTION:
			print "self.STATE_RESOLUTION"
			self.ExGreen_doHide()

	def aspectSelection(self):
		selection = 0
		tlist = []
		tlist.append((_("Resolution"), "resolution"))
		tlist.append(("", ""))
		tlist.append((_("Letterbox"), "letterbox"))
		tlist.append((_("PanScan"), "panscan"))
		tlist.append((_("Non Linear"), "non"))
		tlist.append((_("Bestfit"), "bestfit"))
		mode = open("/proc/stb/video/policy").read()[:-1]
		print mode
		for x in range(len(tlist)):
			if tlist[x][1] == mode:
				selection = x
		keys = ["green", "",  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]
		self.session.openWithCallback(self.aspectSelected, ChoiceBox, title=_("Please select an aspect ratio..."), list = tlist, selection = selection, keys = keys)

	def aspectSelected(self, aspect):
		if not aspect is None:
			if isinstance(aspect[1], str):
				if aspect[1] == "resolution":
					self.ExGreen_toggleGreen()
				else:
					open("/proc/stb/video/policy", "w").write(aspect[1])
					self.ExGreen_doHide()
		return

#------------------------------------------------------------------------------------------
#----------------------------------  MainMenuList   ---------------------------------------
#------------------------------------------------------------------------------------------

class MainMenuList(MenuList):

	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 24))
		self.l.setFont(2, gFont("Regular", 18))
		self.l.setFont(3, gFont("Regular", 22))
		self.listCompleted = []
		self.callback = None
		self.idx = 0
		self.thumb = ""
		self.pos = 20
		##print "[Foreca] MainMenuList"

#--------------------------- Go through all list entries ----------------------------------

	def buildEntries(self):
		##print "[Foreca] buildEntries:", len(self.list)
		if self.idx == len(self.list):
			self.setList(self.listCompleted)
			if self.callback:
				self.callback()
		else:
			self.downloadThumbnail()

	def downloadThumbnail(self):
		thumbUrl = self.list[self.idx][0]
		windlink = self.list[self.idx][3]
		self.thumb = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/thumb/" + str(thumbUrl+ ".png")
		self.wind = resolveFilename(SCOPE_PLUGINS) + "Extensions/Foreca/thumb/" + str(windlink)
		self.buildEntry(None)

#----------------------------------- Build entries for list -------------------------------

	def buildEntry(self, picInfo=None):
		self.x = self.list[self.idx]
		#list.append([thumbnails[x], zeit[x], temp[x], windlink[x], wind[x], Satz1, Satz2, Satz3])
		self.res = [(self.x[0], self.x[1])]

		pngpic = LoadPixmap(self.thumb)
		if pngpic is not None:
			#self.res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 100, 5, 80, 80, png))
			self.res.append(MultiContentEntryPixmapAlphaTest(pos=(95, 5), size=(80, 80), png=pngpic))

		mediumvioletred = 0xC7D285
		rot = 16711680
		gruen = 0x4ad53b
		dgruen = 0x339229
		hlila = 0xffbbff
		hlila2 = 0xee30a7
		drot = 0xff3030
		hrot = 0xff3030
		orange =0xf47d19
		gelb =0xffff00
		mblau = 0x87cefa
		hblau = 0x00c5cd
		dblau = 0x009acd
		ddblau = 0x00688b
		weiss = 0xffffff
		hweiss =0xf7f7f7
		grau = 0x565656
		schwarz = 0x000000

		self.temptext = _("Temp")
		self.tempcolor = hlila
		if int(self.x[2]) >= 1:
			self.tempcolor = mblau
		if int(self.x[2]) >= 5:
			self.tempcolor = hblau
		if int(self.x[2]) >= 10:
			self.tempcolor = gruen
		if int(self.x[2]) >= 15:
			self.tempcolor = gelb
		if int(self.x[2]) >= 20:
			self.tempcolor = orange
		if int(self.x[2]) >= 25:
			self.tempcolor = drot
		if int(self.x[2]) <= 0:
			self.tempcolor = mblau
		if int(self.x[2]) <= -4:
			self.tempcolor = dblau
		if int(self.x[2]) <= -8:
			self.tempcolor = ddblau

		# Time
		self.res.append(MultiContentEntryText(pos=(10, 26), size=(70, 24), font=0, text=self.x[1], color=weiss, color_sel=weiss))

		# Temp
		self.res.append(MultiContentEntryText(pos=(215, 13), size=(80, 24), font=0, text=_("Temp"), color=weiss, color_sel=weiss))
		self.res.append(MultiContentEntryText(pos=(207, 39), size=(80, 24), font=1, text=self.x[2], color=self.tempcolor, color_sel=self.tempcolor))
		self.res.append(MultiContentEntryText(pos=(248, 39), size=(80, 24), font=1, text=_("°C"),  color=self.tempcolor, color_sel=self.tempcolor))
                
		# Wind
		self.res.append(MultiContentEntryText(pos=(339, 13), size=(125, 24), font=0, text=_("Wind"), color=weiss, color_sel=weiss))
		self.res.append(MultiContentEntryText(pos=(325, 39), size=(125, 24), font=1, text=self.x[4], color=mediumvioletred, color_sel=mediumvioletred))

		# Text
		self.res.append(MultiContentEntryText(pos=(445, 5), size=(600, 28), font=3, text=self.x[5], color=weiss, color_sel=weiss))
		self.res.append(MultiContentEntryText(pos=(445, 31), size=(380, 24), font=2, text=self.x[6], color=mblau, color_sel=mblau))
		self.res.append(MultiContentEntryText(pos=(445, 55), size=(380, 24), font=2, text=self.x[7], color=mblau, color_sel=mblau))

		pngpic = LoadPixmap(self.wind + ".png")
		if pngpic is not None:
			self.res.append(MultiContentEntryPixmapAlphaTest(pos=(288, 26), size=(27, 28), png=pngpic))

		self.listCompleted.append(self.res)
		self.idx += 1
		self.buildEntries()

# -------------------------- Build Menu list ----------------------------------------------

	def SetList(self, l):
		##print "[Foreca] SetList"
		self.list = l
		self.l.setItemHeight(90)
		del self.listCompleted
		self.listCompleted = []
		self.idx = 0
		self.buildEntries()

#------------------------------------------------------------------------------------------
#------------------------------------------ Spinner ---------------------------------------
#------------------------------------------------------------------------------------------

class ForecaPreviewCache(Screen):

	skin = """<screen position="center,center" size="76,76" flags="wfNoBorder" backgroundColor="#000000" >
		<eLabel position="2,2" zPosition="1" size="72,72" font="Regular;18" backgroundColor="#40000000" />
		<widget name="spinner" position="14,14" zPosition="4" size="48,48" alphatest="on" />
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
		self.timer.start(120, False)

	def stop(self):
		self.hide()
		self.timer.stop()

	def showNextSpinner(self):
		self.curr += 1
		if self.curr > 10:
			self.curr = 0
		png = LoadPixmap(cached=True, path=PNG_PATH + str(self.curr) + ".png")
		self["spinner"].instance.setPixmap(png)

#------------------------------------------------------------------------------------------
#------------------------------ Foreca Preview---------------------------------------------
#------------------------------------------------------------------------------------------

class ForecaPreview(Screen, HelpableScreen):

	def __init__(self, session):
		global MAIN_PAGE, menu
		self.session = session
		MAIN_PAGE = _("http://www.foreca.com")

		# actual, local Time as Tuple
		lt = localtime()
		# Extract the Tuple, Date
		jahr, monat, tag = lt[0:3]
		heute ="%04i%02i%02i" % (jahr,monat,tag)
		self.tag = 0

		# Get favorites
		global fav1, fav2
		if fileExists(USR_PATH + "/fav1.cfg"):
			file = open(USR_PATH + "/fav1.cfg","r")
			fav1 = str(file.readline().strip())
			file.close()
			fav1 = fav1[fav1.find("/")+1:len(fav1)]
		else:
			fav1 = _("New_York_City")
		if fileExists(USR_PATH + "/fav2.cfg"):
			file = open(USR_PATH + "/fav2.cfg","r")
			fav2 = str(file.readline().strip())
			file.close()
			fav2 = fav2[fav2.find("/")+1:len(fav2)]
		else:
			fav2 = _("Moskva")

		# Get home location
		global city, start
		if fileExists(USR_PATH + "/startservice.cfg"):
			file = open(USR_PATH + "/startservice.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
			start = self.ort[self.ort.find("/")+1:len(self.ort)]
		else:
			self.ort =_("United_Kingdom/London")
			start = _("London")

		# Get diacritics to handle
		self.FILTERin = []
		self.FILTERout = []
		self.FILTERidx = 0
		self.taal = language.getLanguage()[:2]
		if fileExists(USR_PATH + "/Filter.cfg"):
			file = open(USR_PATH + "/Filter.cfg","r")
			for line in file:
				regel = str(line)
				if regel[:2] == self.taal:
					if regel[4] == "Y":
						self.FILTERidx += 1
						self.FILTERin.append(regel[7:15].strip())
						self.FILTERout.append(regel[17:].strip())
		file.close
		
		MAIN_PAGE = _("http://www.foreca.com") + "/" + self.ort + "?lang=" + self.taal + "&details=" + heute + "&units=metrickmh&tf=24h"
		
		desktop = getDesktop(0)
		size = desktop.size()
		width = size.width()
		print "Desktop ", size, width
		if width == 1280:
			self.skin = "<screen position=\"center,center\" size=\"970,505\" title=\"" + _("Foreca Weather Forecast") + "\" backgroundColor=\"#40000000\" >"
			self.skin += """<widget name="MainList" position="0,90" size="970,365" zPosition="3" backgroundColor="#40000000" backgroundColorSelected="#565656" selectionDisabled="1" scrollbarMode="showOnDemand" />
				<widget source="Titel" render="Label" position="4,10" zPosition="3" size="968,40" font="Regular;30" valign="center" halign="center" transparent="1" foregroundColor="#ffffff"/>
				<widget source="Titel2" render="Label" position="299,15" zPosition="2" size="440,40" font="Regular;28" valign="center" halign="left" transparent="1" foregroundColor="#f47d19"/>
				<eLabel position="5,70" zPosition="2" size="970,1" backgroundColor="#FFFFFF" />
				<widget source="key_red" render="Label" position="39,463" zPosition="2" size="102,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_green" render="Label" position="177,463" zPosition="2" size="102,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_yellow" render="Label" position="315,463" zPosition="2" size="102,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_blue" render="Label" position="453,463" zPosition="2" size="102,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_ok" render="Label" position="591,463" zPosition="2" size="138,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_menu" render="Label" position="729,463" zPosition="2" size="138,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_info" render="Label" position="867,463" zPosition="2" size="138,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<ePixmap position="2,470" size="36,25" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="140,470" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
				<ePixmap position="278,470" size="36,25" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="416,470" size="36,25" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				<ePixmap position="554,470" size="36,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" transparent="1" alphatest="on" />
				<ePixmap position="692,470" size="36,25" pixmap="skin_default/buttons/key_menu.png" transparent="1" alphatest="on" />
				<ePixmap position="830,470" size="36,25" pixmap="skin_default/buttons/key_info.png" transparent="1" alphatest="on" />
				<eLabel position="5,460" zPosition="2" size="970,2" backgroundColor="#FFFFFF" />
			</screen>"""
		else:
			self.skin = "<screen position=\"center,65\" size=\"899,480\" title=\"" + _("Foreca Weather Forecast") + "\" backgroundColor=\"#40000000\" >"
			self.skin += """<widget name="MainList" position="0,65" size="899,363" zPosition="3" backgroundColor="#40000000" backgroundColorSelected="#565656" selectionDisabled="1" scrollbarMode="showOnDemand" />
				<widget source="Titel" render="Label" position="120,3" zPosition="3" size="740,40" font="Regular;36" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="Titel2" render="Label" position="288,5" zPosition="2" size="440,40" font="Regular;28" valign="center" halign="left" transparent="1" foregroundColor="#f47d19"/>
				<eLabel position="5,55" zPosition="2" size="870,1" backgroundColor="#FFFFFF" />
				<widget source="key_red" render="Label" position="70,438" zPosition="2" size="200,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_green" render="Label" position="260,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="key_yellow" render="Label" position="450,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="key_blue" render="Label" position="640,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="key_ok" render="Label" position="773,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<ePixmap position="27,442" size="36,25" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="217,442" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
				<ePixmap position="407,442" size="36,25" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="597,442" size="36,25" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				<ePixmap position="730,442" size="36,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/buttons/key_ok.png" transparent="1" alphatest="on" />
				<eLabel position="5,437" zPosition="2" size="870,2" backgroundColor="#FFFFFF" />
			</screen>"""

		Screen.__init__(self, session)
		#self["navigationTitle"] = Label(" ")
		self["MainList"] = MainMenuList()
		self["Titel"] = StaticText()
		self["Titel2"] = StaticText(_("Please wait ..."))
		self["Titel3"] = StaticText()
		self["key_red"] = StaticText(_("Week"))
		self["key_ok"] = StaticText(_("City"))
		if config.plugins.foreca.citylabels.value == True:
			self["key_green"] = StaticText(fav1)
			self["key_yellow"] = StaticText(fav2)
			self["key_blue"] = StaticText(start)
		else:
			self["key_green"] = StaticText(_("Favorite 1"))
			self["key_yellow"] = StaticText(_("Favorite 2"))
			self["key_blue"] = StaticText(_("Home"))
		self["key_info"] = StaticText(_("Legend"))
		self["key_menu"] = StaticText(_("Maps"))
		self["Title"] = StaticText(_("Foreca Weather Forecast") + "    " + _("Version ") + PluginVersion)

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.exit, _("Exit - End")),
				"menu": (self.Menu, _("Menu - Weather maps")),
				"showEventInfo": (self.info, _("Info - Legend")),
				"ok": (self.OK, _("OK - City")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"red": (self.red, _("Red - Weekoverview")),
				"green": (self.Fav1, _("Green - Favorite 1")),
				"yellow": (self.Fav2, _("Yellow - Favorite 2")),
				"blue": (self.Fav0, _("Blue - Home")),
				"0": (self.Tag0, _("0 - Today")),
				"1": (self.Tag1, _("1 - Today + 1 day")),
				"2": (self.Tag2, _("2 - Today + 2 days")),
				"3": (self.Tag3, _("3 - Today + 3 days")),
				"4": (self.Tag4, _("4 - Today + 4 days")),
				"5": (self.Tag5, _("5 - Today + 5 days")),
				"6": (self.Tag6, _("6 - Today + 6 days")),
				"7": (self.Tag7, _("7 - Today + 7 days")),
				"8": (self.Tag8, _("8 - Today + 8 days")),
				"9": (self.Tag9, _("9 - Today + 9 days")),
			}, -2)

		self.StartPageFirst()

	def StartPageFirst(self):
		##print "[Foreca] StartPageFirst:"
		self.cacheDialog = self.session.instantiateDialog(ForecaPreviewCache)
		self["MainList"].callback = self.deactivateCacheDialog
		self.working = False
		self["MainList"].show
		self.cacheTimer = eTimer()
		self.cacheDialog.start()
		self.onLayoutFinish.append(self.getPage)

	def if1730down(self):
		lt = localtime()
		jahr, monat, tag, stunde, minute = lt[0:5]
		if not self.working and self.tag == 0:
			if ((stunde * 60) + minute) >= ((17 * 60) + 30):
				self["MainList"].pageUp()
				self["MainList"].pageUp()
				self["MainList"].pageDown()

	def StartPage(self):
		self["Titel"].text = "                                   "
		self["Titel3"].text = "                  \r\n                 "
		self["Titel2"].text = _("Please wait ...")
		self.working = False
		print "[Foreca] MainList show:"
		self["MainList"].show
		self.getPage()

	def getPage(self, page=None):
		print "[Foreca] getPage:"
		self.cacheDialog.start()
		self.working = True
		if not page:
			page = ""
		url = "%s%s"%(MAIN_PAGE, page)
		print "[Foreca] Url:" , url
		getPage(url).addCallback(self.getForecaPage).addErrback(self.error)

	def error(self, err=""):
		print "[Foreca] Error:", err
		self.working = False
		self.deactivateCacheDialog()

	def deactivateCacheDialog(self):
		self.cacheDialog.stop()
		self.working = False

	def exit(self):
		try:
			os.unlink("/tmp/sat.jpg")
		except:
			pass
		try:
			os.unlink("/tmp/sat.html")
		except:
			pass
		try:
			os.unlink("/tmp/meteogram.png")
		except:
			pass
		self.close()
		self.deactivateCacheDialog()

	def Tag0(self):
		self.Zukunft(0)

	def Tag1(self):
		self.Zukunft(1)

	def Tag2(self):
		self.Zukunft(2)

	def Tag3(self):
		self.Zukunft(3)

	def Tag4(self):
		self.Zukunft(4)

	def Tag5(self):
		self.Zukunft(5)

	def Tag6(self):
		self.Zukunft(6)

	def Tag7(self):
		self.Zukunft(7)

	def Tag8(self):
		self.Zukunft(8)

	def Tag9(self):
		self.Zukunft(9)

	def Fav0(self):
		global start
		if fileExists(USR_PATH + "/startservice.cfg"):
			file = open(USR_PATH + "/startservice.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort =_("United_Kingdom/London")
		start = self.ort[self.ort.find("/")+1:len(self.ort)]
		self.Zukunft(0)

	def Fav1(self):
		global fav1
		if fileExists(USR_PATH + "/fav1.cfg"):
			file = open(USR_PATH + "/fav1.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort =_("United_States/New_York_City")
		fav1 = self.ort[self.ort.find("/")+1:len(self.ort)]
		self.Zukunft(0)

	def Fav2(self):
		global fav2
		if fileExists(USR_PATH + "/fav2.cfg"):
			file = open(USR_PATH + "/fav2.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort =_("Russia/Moskva")
		fav2 = self.ort[self.ort.find("/")+1:len(self.ort)]
		self.Zukunft(0)

	def Zukunft(self, ztag=0):
		global MAIN_PAGE
		# actual, local Time as Tuple
		lt = localtime()
		jahr, monat, tag = lt[0:3]

		# Calculate future date
		ntag = tag + ztag
		zukunft = jahr, monat, ntag, 0, 0, 0, 0, 0, 0
		morgen = mktime(zukunft)
		lt = localtime(morgen)
		jahr, monat, tag = lt[0:3]
		morgen ="%04i%02i%02i" % (jahr,monat,tag)

		MAIN_PAGE = _("http://www.foreca.com") + "/" + self.ort + "?lang=" + self.taal + "&details=" + morgen + "&units=metrickmh&tf=24h"
		##print "Taglink ", MAIN_PAGE

		# Show in Gui
		self.StartPage()

	def OK(self):
		global city
		panelmenu = ""
		city = self.ort
		self.session.openWithCallback(self.OKCallback, CityPanel,panelmenu)

	def info(self):
		message = "%s" % (_("\n0 - 9       =   Prognosis (x) days from now\n\nVOL+/-  =   Fast scroll (City choice)\n\n<   >       =   Prognosis next/previous day\n\nInfo        =   This information\n\nMenu     =   Satellite photos and maps\n\nRed        =   Temperature for the next 5 days\n\nGreen    =   Go to Favorite 1\n\nYellow    =   Go to Favorite 2\n\nBlue        =   Go to Home\n\nWind direction = Arrow to right: Wind from the West\n"))
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO)

	def OKCallback(self):
		global city, fav1, fav2
		self.ort = city
		self.tag = 0
		self.Zukunft(0)
		if config.plugins.foreca.citylabels.value == True:
			self["key_green"].setText(fav1)
			self["key_yellow"].setText(fav2)
			self["key_blue"].setText(start)
		else:
			self["key_green"].setText(_("Favorite 1"))
			self["key_yellow"].setText(_("Favorite 2"))
			self["key_blue"].setText(_("Home"))
		##print "MenuCallback "

	def Menu(self):
		self.session.openWithCallback(self.MenuCallback, SatPanel, self.ort)

	def MenuCallback(self):
		global menu, start, fav1, fav2
		if config.plugins.foreca.citylabels.value == True:
			self["key_green"].setText(fav1)
			self["key_yellow"].setText(fav2)
			self["key_blue"].setText(start)
		else:
			self["key_green"].setText(_("Favorite 1"))
			self["key_yellow"].setText(_("Favorite 2"))
			self["key_blue"].setText(_("Home"))
		self.if1730down()

#
#------------------------------------------------------------------------------------------

	def loadPicture(self,url=""):
		devicepath = "/tmp/meteogram.png"
		path = "/tmp"
		h = urllib.urlretrieve(url, devicepath)
		filelist = devicepath
		self.session.open(PicView, filelist, 0, path, False)

#------------------------------------------------------------------------------------------

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
			self["MainList"].up()

	def down(self):
		if not self.working:
			self["MainList"].down()

	def red(self):
		if not self.working:
			#self.loc_id = current id
			self.url=_("http://www.foreca.com") + "/meteogram.php?loc_id=" + self.loc_id + "&lang=" + self.taal + "&units=metrickmh/meteogram.png"
			self.loadPicture(self.url)

# ----------------------------------------------------------------------

	def getForecaPage(self,html):
		#new Ajax.Request('/lv?id=102772400', {
		fulltext = re.compile(r"new Ajax.Request.+?lv.+?id=(.+?)'", re.DOTALL)
		id = fulltext.findall(html)
		self.loc_id = str(id[0])

		# <!-- START -->
		#<h6><span>Tuesday</span> March 29</h6>

		##print "[Foreca] Start:" + str(len(html))
		fulltext = re.compile(r'<!-- START -->.+?<h6><span>(.+?)</h6>', re.DOTALL)
		titel = fulltext.findall(html)
		titel[0] = str(sub('<[^>]*>',"",titel[0]))
		#print titel[0]
		#self["Titel"].setText(titel[0])

		# <a href="/Austria/Linz?details=20110330">We</a>
		fulltext = re.compile(r'<!-- START -->(.+?)<h6>', re.DOTALL)
		link = str(fulltext.findall(html))
		#print link

		fulltext = re.compile(r'<a href=".+?>(.+?)<.+?', re.DOTALL)
		tag = str(fulltext.findall(link))
		#print "Day ", tag

		# ---------- Wetterdaten -----------

		# <div class="row clr0">
		fulltext = re.compile(r'<!-- START -->(.+?)<div class="datecopy">', re.DOTALL)
		html = str(fulltext.findall(html))

		##print "searching ....."
		list = []

		fulltext = re.compile(r'<a href="(.+?)".+?', re.DOTALL)
		taglink = str(fulltext.findall(html))
		#taglink = konvert_uml(taglink)
		#print "Daylink ", taglink

		fulltext = re.compile(r'<a href=".+?>(.+?)<.+?', re.DOTALL)
		tag = fulltext.findall(html)
		#print "Day ", str(tag)

		# <div class="c0"> <strong>17:00</strong></div>
		fulltime = re.compile(r'<div class="c0"> <strong>(.+?)<.+?', re.DOTALL)
		zeit = fulltime.findall(html)
		#print "Time ", str(zeit)

		#<div class="c4">
		#<span class="warm"><strong>+15&deg;</strong></span><br />
		fulltime = re.compile(r'<div class="c4">.*?<strong>(.+?)&.+?', re.DOTALL)
		temp = fulltime.findall(html)
		#print "Temp ", str(temp)

		# <div class="symbol_50x50d symbol_d000_50x50" title="clear"
		fulltext = re.compile(r'<div class="symbol_50x50.+? symbol_(.+?)_50x50.+?', re.DOTALL)
		thumbnails = fulltext.findall(html)

		fulltext = re.compile(r'<div class="c3">.+? (.+?)<br />.+?', re.DOTALL)
		titel1 = fulltext.findall(html)
		#print "Title ", str(titel1).lstrip("\t").lstrip()

		fulltext = re.compile(r'<div class="c3">.+?<br />(.+?)</strong>.+?', re.DOTALL)
		titel2 = fulltext.findall(html)
		#print "Title ", str(titel2).lstrip("\t").lstrip()

		fulltext = re.compile(r'<div class="c3">.+?</strong><br />(.+?)</.+?', re.DOTALL)
		titel3 = fulltext.findall(html)
		#print "Title ", str(titel3).lstrip("\t").lstrip()

		fulltext = re.compile(r'<div class="c2">.+?<img src="/img/symb-wind/(.+?).gif', re.DOTALL)
		windlink = fulltext.findall(html)
		#print "Windlink ", str(windlink)

		fulltext = re.compile(r'<div class="c2">.+?<strong>(.+?)<.+?', re.DOTALL)
		wind = fulltext.findall(html)
		#print "Wind ", str(wind)
		#print "--------------------------------------------"

		wert = len(zeit)

		x = 0
		while x < wert:
			titel1[x] = str(sub('<[^>]*>',"",titel1[x]))
			#Text1 = titel1[x]
			Satz1 = self.konvert_uml(titel1[x])
			titel2[x] = str(sub('<[^>]*>',"",titel2[x]))
			#Text2 = titel2[x]
			Satz2 = self.konvert_uml(titel2[x])
			titel3[x] = str(sub('<[^>]*>',"",titel3[x]))
			#Text3 = titel3[x]
			Satz3 = self.konvert_uml(titel3[x])
			wind[x] = self.filter_dia(wind[x])
			#print zeit[x]
			#print tag[x]
			#print temp[x]
			#print windlink[x]
			#print wind[x]
			#print Satz1
			#print Satz2
			#print Satz3
			#print "--------------------------------------------"
			list.append([thumbnails[x], zeit[x], temp[x], windlink[x], wind[x], Satz1, Satz2, Satz3])
			x = x +1

		self["Titel2"].text = "                                   "
		datum = titel[0]
		foundPos=datum.rfind(" ")
		foundPos2=datum.find(" ")
		datum2=datum[0:foundPos2]+datum[foundPos:len(datum)]+datum[foundPos2:foundPos]
		foundPos=self.ort.find("/")
		plaats=_(self.ort[0:foundPos]) + "-" + self.ort[foundPos+1:len(self.ort)]
		self["Titel"].text = _(plaats) + "  -  " + datum2
		self["Titel3"].text = _(self.ort[0:foundPos]) + "\r\n" + self.ort[foundPos+1:len(self.ort)] + "\r\n" + datum2
		self["MainList"].SetList(list)
		self["MainList"].selectionEnabled(1)
		self["MainList"].show
		self.if1730down()

#------------------------------------------------------------------------------------------
	def konvert_uml(self,Satz):
		Satz = self.filter_dia(Satz)
		# remove remaining control characters and return
		return Satz[Satz.rfind("\\t")+2:len(Satz)]	

	def filter_dia(self, Satz):
		# remove diacritics for selected country
		tel = 0
		while tel < self.FILTERidx:
			Satz = string.replace(Satz, self.FILTERin[tel], self.FILTERout[tel])
			tel += 1
		return Satz
# -------------------------------------------------------------------
class CityPanelList(MenuList):
	def __init__(self, list, font0 = 22, font1 = 16, itemHeight = 30, enableWrapAround = True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", font0))
		self.l.setFont(1, gFont("Regular", font1))
		self.l.setItemHeight(itemHeight)

# -------------------------------------------------------------------

class CityPanel(Screen, HelpableScreen):

	def __init__(self, session, panelmenu):
		self.session = session
		self.skin = "<screen name=\"CityPanel\" position=\"center,center\" size=\"730,540\" title=\"" + _("Select a city") + "\" backgroundColor=\"#40000000\">"
		self.skin += """<widget name="Mlist" position="10,10" size="700,490" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			<eLabel position="0,515" zPosition="2" size="630,1" backgroundColor="#c1cdc1" />
			<widget source="key_green" render="Label" position="40,512" zPosition="2" size="150,30" font="Regular;20" valign="center" halign="left" transparent="1" />
			<widget source="key_yellow" render="Label" position="190,512" zPosition="2" size="150,30" font="Regular;20" valign="center" halign="left" transparent="1" />
			<widget source="key_blue" render="Label" position="340,514" zPosition="2" size="350,30" font="Regular;20" valign="center" halign="left" transparent="1" />
			<ePixmap position="0,515" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
			<ePixmap position="150,515" size="36,25" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="300,515" size="36,25" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
			</screen>"""

		Screen.__init__(self, session)
		self.Mlist = []

		self.maxidx = 0
		if fileExists(USR_PATH + "/City.cfg"):
			file = open(USR_PATH + "/City.cfg", "r")
			for line in file:
				text = line.strip()
				self.maxidx += 1
				self.Mlist.append(self.CityEntryItem((_(text), text)))
			file.close

		self.onChangedEntry = []
		self["Mlist"] = CityPanelList([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)

		self["key_green"] = StaticText(_("Favorite 1"))
		self["key_yellow"] = StaticText(_("Favorite 2"))
		self["key_blue"] = StaticText(_("Home"))
		self["Title"] = StaticText(_("Select a city"))

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self,"AAFKeyActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"ok": (self.ok, _("OK - Select")),
				"green": (self.green, _("Green - Favorite 1")),
				"yellow": (self.yellow, _("Yellow - Favorite 2")),
				"blue": (self.blue, _("Blue - Home")),
				"nextBouquet": (self.jump500_down, _("Channel+ - 500 back")),
				"prevBouquet": (self.jump500_up, _("Channel- - 500 forward")),
				"volumeDown": (self.jump100_up, _("Volume- - 100 forward")),
				"volumeUp": (self.jump100_down, _("Volume+ - 100 back"))
			}, -2)

	def jump500_up(self):
		cur = self["Mlist"].l.getCurrentSelectionIndex()
		if (cur + 500) <= self.maxidx:
			self["Mlist"].instance.moveSelectionTo(cur + 500)
		else:
			self["Mlist"].instance.moveSelectionTo(self.maxidx -1)

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
			self["Mlist"].instance.moveSelectionTo(self.maxidx -1)

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

	def Exit(self):
		self.close()

	def ok(self):
		global city
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "Press OK", city
		self.close()

	def blue(self):
		global start
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "[Foreca] Service:", city
		fwrite = open(USR_PATH + "/startservice.cfg", "w")
		fwrite.write(city)
		fwrite.close()
		start = city[city.find("/")+1:len(city)]
		message = "%s %s" % (_("This city is stored as home!\n\n                                  "), city)
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=3)

	def green(self):
		global fav1
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "[Foreca] Service:", city
		fwrite = open(USR_PATH + "/fav1.cfg", "w")
		fwrite.write(city)
		fwrite.close()
		fav1 = city[city.find("/")+1:len(city)]
		message = "%s %s" % (_("This city is stored as favorite 1!\n\n                             "), city)
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=3)

	def yellow(self):
		global fav2
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "[Foreca] Service:", city
		fwrite = open(USR_PATH + "/fav2.cfg", "w")
		fwrite.write(city)
		fwrite.close()
		fav2 = city[city.find("/")+1:len(city)]
		message = "%s %s" % (_("This city is stored as favorite 2!\n\n                             "), city)
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=3)

	def CityEntryItem(self,entry):
		rot = 16711680
		gruen = 0x4ad53b
		dgruen = 0x339229
		drot = 0xf47d19
		mblau = 8900346
		hblau = 11592447
		dblau = 5215437
		weiss = 0xffffff
		orange = 0xf47d19
		grau = 0x565656

		res = [entry]
		#return (eListboxPythonMultiContent.TYPE_TEXT, pos[0], pos[1], size[0], size[1], font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)
		#res.append(MultiContentEntryPixmapAlphaTest(pos=(2, 5), size=(100, 60), png=entry[0]))  # png vorn
		res.append(MultiContentEntryText(pos=(30, 6), size=(600, 35), font=0, text=entry[0], color=weiss, color_sel=mblau, backcolor_sel=grau))
		return res

#------------------------------------------------------------------------------------------
#    Europe Maps
# -----------------------------------------------------------------------------------------

class SatPanelList(MenuList):

	if (getDesktop(0).size().width() == 1280):
		ItemSkin = 142
	else:
		ItemSkin = 122

	def __init__(self, list, font0 = 28, font1 = 16, itemHeight = ItemSkin, enableWrapAround = True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", font0))
		self.l.setFont(1, gFont("Regular", font1))
		self.l.setItemHeight(itemHeight)

# -----------------------------------------------------------------------------------------

class SatPanel(Screen, HelpableScreen):

	def __init__(self, session, ort):
		self.session = session
		self.ort = ort

		if (getDesktop(0).size().width() == 1280):
			self.skin = "<screen name=\"SatPanel\" position=\"center,center\" size=\"630,500\" title=\"" + _("Satellite photos") + "\" backgroundColor=\"#40000000\">"
			self.skin += """<widget name="Mlist" position="10,10" size="600,430" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
				<eLabel position="0,445" zPosition="2" size="630,1" backgroundColor="#c1cdc1" />
				<widget source="key_red" render="Label" position="40,450" zPosition="2" size="124,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_green" render="Label" position="198,450" zPosition="2" size="140,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_yellow" render="Label" position="338,450" zPosition="2" size="140,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_blue" render="Label" position="498,450" zPosition="2" size="142,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<ePixmap position="2,460" size="36,20" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="160,460" size="36,20" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
				<ePixmap position="300,460" size="36,20" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="460,460" size="36,20" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				</screen>"""
		else:
			self.skin = "<screen name=\"SatPanel\" position=\"center,center\" size=\"630,440\" title=\"" + _("Satellite photos") + "\" backgroundColor=\"#252525\">"
			self.skin += """<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#252525"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
				<eLabel position="0,385" zPosition="2" size="630,1" backgroundColor="#c1cdc1" />
				<widget source="key_red" render="Label" position="40,397" zPosition="2" size="124,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_green" render="Label" position="198,397" zPosition="2" size="140,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_yellow" render="Label" position="338,397" zPosition="2" size="140,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_blue" render="Label" position="498,397" zPosition="2" size="142,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<ePixmap position="2,400" size="36,20" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="160,400" size="36,20" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
				<ePixmap position="300,400" size="36,20" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="460,400" size="36,20" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				</screen>"""

		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('satelliet'), _("Weather map Video"), 'satelliet')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('neerslag'), _("Showerradar Video"), 'neerslag')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('bewolking'), _("Cloudcover Video"), 'bewolking')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('eumetsat'), _("Eumetsat"), 'eumetsat')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('luchtdruk'), _("Air pressure"), 'luchtdruk')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('infrarotmetoffice'), _("Infrared"), 'infrarotmetoffice')))
                
		self.onChangedEntry = []
		self["Mlist"] = SatPanelList([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_red"] = StaticText(_("Continents"))
		self["key_green"] = StaticText(_("Europe"))
		self["key_yellow"] = StaticText(_("Germany"))
		self["key_blue"] = StaticText(_("Settings"))
		self["Title"] = StaticText(_("Satellite photos"))

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"red": (self.SatPanelc, _("Red - Continents")),
				"green": (self.SatPaneld, _("Green - Europe")),
				"yellow": (self.SatPanelb, _("Yellow - Germany")),
				"blue": (self.PicSetupMenu, _("Blue - Settings")),
				"ok": (self.ok, _("OK - Show")),
			}, -2)

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
		#global menu
		menu = self['Mlist'].l.getCurrentSelection()[0][2]
		##print "Press OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/thumb/" + file + ".png")
		res = (png)
		return res

	def SatPanelb(self):
		self.session.open(SatPanelb, self.ort)

	def SatPanelc(self):
		self.session.open(SatPanelc, self.ort)

	def SatPaneld(self):
		self.session.open(SatPaneld, self.ort)

	def PicSetupMenu(self):
		self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satellitephotos are being loaded .....\n\n                       "))
		#self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=4)

		menu = self['Mlist'].l.getCurrentSelection()[0][2]
		if menu == "satelliet":
			# http://www.foreca.de/Austria/Linz?map=sat
			devicepath = "/tmp/sat.html"
			url = _("http://www.foreca.com") + "/" + self.ort + "?map=sat"

#------------------------------------------------------------------------------------------

		if menu == "neerslag":
			devicepath = "/tmp/sat.html"
			url = _("http://www.foreca.com") + "/" + self.ort + "?map=rain"

#------------------------------------------------------------------------------------------

		if menu == "bewolking":
			devicepath = "/tmp/sat.html"
			url = _("http://www.foreca.com") + "/" + self.ort + "?map=cloud"

#------------------------------------------------------------------------------------------

		if menu == "luchtdruk":
			devicepath = "/tmp/sat.html"
			url = _("http://www.foreca.com") + "/" + self.ort + "?map=pressure"

#------------------------------------------------------------------------------------------

		if menu == "satelliet" or menu == "neerslag" or menu == "bewolking" or menu == "luchtdruk":
			# Load site for category and search Picture link
			h = urllib.urlretrieve(url, devicepath)
			fd=open(devicepath)
			html=fd.read()
			fd.close()

			fulltext = re.compile(r'http://cache-(.+?) ', re.DOTALL)
			PressureLink = fulltext.findall(html)
			PicLink = PressureLink[0]
			PicLink = "http://cache-" +	PicLink

			# Load Picture for Slideshow
			devicepath = resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/bilder/"
			max = int(len(PressureLink))-2
			print "max= ", str(max)
			zehner = "1"
			x = 0
			while x < max:
				url = "http://cache-" + PressureLink[x]
				print str(x), url
				foundPos = url.find("0000.jpg")
				print foundPos
				if foundPos ==-1:
					foundPos = url.find(".jpg")
				if foundPos ==-1:
					foundPos = url.find(".png")
				file = int(url[foundPos-6:foundPos])
				print str(file)
				file = file + 2
				print str(file)
				file = str(file)
				file2 = file[2:4]+"-"+file[0:2]+" - "+file[4:6]+" "+_("h")
				print file2
				h = urllib.urlretrieve(url, devicepath + file2 + ".jpg")
				x = x + 1
				if x > 9:
					zehner = "2"

			self.session.open(View_Slideshow, 0, True)

		else:
			if menu == "eumetsat":
				devicepath = "/tmp/meteogram.png"
				path = "/tmp"
				h = urllib.urlretrieve("http://www.sat24.com/images.php?country=eu&type=zoom&format=640x480001001&rnd=118538", devicepath)
				filelist = devicepath
				self.session.open(PicView, filelist, 0, path, False)

			if menu == "infrarotmetoffice":
				# http://www.metoffice.gov.uk/satpics/latest_IR.html
				devicepath = "/tmp/sat.html"
				url = "http://www.metoffice.gov.uk/satpics/latest_IR.html"
				path = "/tmp"
				h = urllib.urlretrieve(url, devicepath)
				fd=open(devicepath)
				html=fd.read()
				fd.close()

				#http://www.metoffice.gov.uk/weather/images/eurir_sat_201104251500.jpg
				# <img src='/weather/images/eurir_sat_201104251500.jpg' name="sat"
				fulltext = re.compile(r'<img src=\'(.+?)\' name="sat"', re.DOTALL)
				PressureLink = fulltext.findall(html)
				PicLink = "http://www.metoffice.gov.uk" + PressureLink[0]
				print PicLink
				devicepath = "/tmp/meteogram.png"
				path = "/tmp"
				h = urllib.urlretrieve(PicLink, devicepath)
				filelist = devicepath
				self.session.open(PicView, filelist, 0, path, False)

#------------------------------------------------------------------------------------------

	def SatEntryItem(self,entry):
		if (getDesktop(0).size().width() == 1280):
			ItemSkin = 142
		else:
			ItemSkin = 122

		rot = 16711680
		gruen = 0x4ad53b
		dgruen = 0x339229
		tpschwarz = 99000000
		drot = 0xf47d19
		mblau = 8900346
		hblau = 11592447
		dblau = 5215437
		weiss = 0xffffff
		orange = 0xf47d19
		grau = 0x565656
		res = [entry]
		#return (eListboxPythonMultiContent.TYPE_TEXT, pos[0], pos[1], size[0], size[1], font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)
		res.append(MultiContentEntryPixmapAlphaTest(pos=(2, 5), size=(200,ItemSkin -2), png=entry[0]))  # png vorn
		res.append(MultiContentEntryText(pos=(240, 45), size=(340, 50), font=0, text=entry[1], color=weiss, color_sel=mblau, backcolor_sel=grau))
		return res

#------------------------------------------------------------------------------------------
# Bundeslaender - Karten
# -------------------------------------------------------------------

class SatPanelListb(MenuList):

	if (getDesktop(0).size().width() == 1280):
		ItemSkin = 142
	else:
		ItemSkin = 122

	def __init__(self, list, font0 = 28, font1 = 16, itemHeight = ItemSkin, enableWrapAround = True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", font0))
		self.l.setFont(1, gFont("Regular", font1))
		self.l.setItemHeight(itemHeight)

# -------------------------------------------------------------------

class SatPanelb(Screen, HelpableScreen):

	def __init__(self, session, ort):
		self.session = session
		self.ort = ort

		if (getDesktop(0).size().width() == 1280):
			self.skin = "<screen name=\"SatPanelb\" position=\"center,center\" size=\"630,500\" title=\"" + _("Germany") + "\" backgroundColor=\"#40000000\">"
			self.skin += """<widget name="Mlist" position="10,25" size="600,430" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""
		else:
			self.skin = "<screen name=\"SatPanelb\" position=\"center,center\" size=\"630,440\" title=\"" + _("Germany") + "\" backgroundColor=\"#40000000\">"
			self.skin += """<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""


		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('badenwuerttemberg'), _("Baden-Wuerttemberg"), 'badenwuerttemberg')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('bayern'), _("Bavaria"), 'bayern')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('berlin'), _("Berlin"), 'berlin')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('brandenburg'), _("Brandenburg"), 'brandenburg')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('bremen'), _("Bremen"), 'bremen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('hamburg'), _("Hamburg"), 'hamburg')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('hessen'), _("Hesse"), 'hessen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('mecklenburgvorpommern'), _("Mecklenburg-Vorpommern"), 'mecklenburgvorpommern')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('niedersachsen'), _("Lower Saxony"), 'niedersachsen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('nordrheinwestfalen'), _("North Rhine-Westphalia"), 'nordrheinwestfalen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('rheinlandpfalz'), _("Rhineland-Palatine"), 'rheinlandpfalz')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('saarland'), _("Saarland"), 'saarland')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('sachsen'), _("Saxony"), 'sachsen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('sachsenanhalt'), _("Saxony-Anhalt"), 'sachsenanhalt')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('schleswigholstein'), _("Schleswig-Holstein"), 'schleswigholstein')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('thueringen'), _("Thuringia"), 'thueringen')))

		self.onChangedEntry = []
		self["Mlist"] = SatPanelListb([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_blue"] = StaticText(_("Settings"))
		self["Title"] = StaticText(_("Germany"))

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"blue": (self.PicSetupMenu, _("Blue - Settings")),
				"ok": (self.ok, _("OK - Show")),
			}, -2)

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
		#global menu
		menu = self['Mlist'].l.getCurrentSelection()[0][2]
		##print "Press OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/bundesland/" + file + ".png")
		res = (png)
		return res

	def PicSetupMenu(self):
		self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satelitephotos are being loaded .....\n\n                       "))
		#self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=4)

		menu = self['Mlist'].l.getCurrentSelection()[0][2]

		if menu == "badenwuerttemberg":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/badenwuerttemberg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "bayern":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/bayern0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "berlin":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/berlin0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "brandenburg":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/brandenburg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "bremen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/bremen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "hamburg":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/hamburg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "hessen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/hessen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "mecklenburgvorpommern":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/mecklenburgvorpommern0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "niedersachsen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/niedersachsen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "nordrheinwestfalen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/nordrheinwestfalen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "rheinlandpfalz":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/rheinlandpfalz0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "saarland":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/saarland0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "sachsen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/sachsen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "sachsenanhalt":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/sachsenanhalt0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "schleswigholstein":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/schleswigholstein0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "thueringen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/thueringen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)


#------------------------------------------------------------------------------------------

	def SatEntryItem(self,entry):
		if (getDesktop(0).size().width() == 1280):
			ItemSkin = 142
		else:
			ItemSkin = 122

		rot = 16711680
		gruen = 0x4ad53b
		dgruen = 0x339229
		tpschwarz = 99000000
		drot = 0xf47d19
		mblau = 8900346
		hblau = 11592447
		dblau = 5215437
		weiss = 0xffffff
		orange = 0xf47d19
		grau = 0x565656
		res = [entry]
		#return (eListboxPythonMultiContent.TYPE_TEXT, pos[0], pos[1], size[0], size[1], font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)
		res.append(MultiContentEntryPixmapAlphaTest(pos=(2, 5), size=(200,ItemSkin -2), png=entry[0]))  # png vorn
		res.append(MultiContentEntryText(pos=(200, 45), size=(360, 50), font=0, text=entry[1], color=weiss, color_sel=mblau, backcolor_sel=grau))
		return res

#------------------------------------------------------------------------------------------
# Worldmap - Continents
# -------------------------------------------------------------------

class SatPanelListc(MenuList):

	if (getDesktop(0).size().width() == 1280):
		ItemSkin = 92
	else:
		ItemSkin = 92

	def __init__(self, list, font0 = 28, font1 = 16, itemHeight = ItemSkin, enableWrapAround = True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", font0))
		self.l.setFont(1, gFont("Regular", font1))
		self.l.setItemHeight(itemHeight)

# -------------------------------------------------------------------

class SatPanelc(Screen, HelpableScreen):
	def __init__(self, session, ort):
		self.session = session
		self.ort = ort

		if (getDesktop(0).size().width() == 1280):
			self.skin = "<screen name=\"SatPanelc\" position=\"center,center\" size=\"630,500\" title=\"" + _("Continents") + "\" backgroundColor=\"#40000000\">"
			self.skin += """<widget name="Mlist" position="1,20" size="627,460" zPosition="3" backgroundColor="#40000000" backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""                                  
		else:
			self.skin = "<screen name=\"SatPanelc\" position=\"center,center\" size=\"630,440\" title=\"" + _("Continents") + "\" backgroundColor=\"#252525\">"
			self.skin += """<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#252525"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""


		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('europa'), _("Europe"), 'europa')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('afrika-nord'), _("North Africa"), 'afrika-nord')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('afrika-sued'), _("South Africa"), 'afrika-sued')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('nordamerika'), _("North America"), 'nordamerika')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('mittelamerika'), _("Middle America"), 'mittelamerika')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('suedamerika'), _("South America"), 'suedamerika')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('naherosten'), _("Middle East"), 'naherosten')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('ostasien'), _("East Asia"), 'ostasien')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('suedostasien'), _("Southeast Asia"), 'suedostasien')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('zentralasien'), _("Middle Asia"), 'zentralasien')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('australienundozeanien'), _("Australia"), 'australienundozeanien')))
                
		self.onChangedEntry = []
		self["Mlist"] = SatPanelListc([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		#self["key_blue"] = StaticText(_("Settings"))
		self["Title"] = StaticText(_("Continents"))

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				#"blue": (self.PicSetupMenu, _("Blue - Settings")),
				"ok": (self.ok, _("OK - Show")),
			}, -2)

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
		#global menu
		menu = self['Mlist'].l.getCurrentSelection()[0][2]
		##print "Press OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/kontinent/" + file + ".png")
		res = (png)
		return res

	#def PicSetupMenu(self):
		#self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satelitephotos are being loaded .....\n\n                       "))
		#self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=4)

		menu = self['Mlist'].l.getCurrentSelection()[0][2]

		if menu == "europa":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/europa0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "afrika-nord":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/afrika_nord0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "afrika-sued":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/afrika_sued0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)
                        
		if menu == "nordamerika":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/nordamerika0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "mittelamerika":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/mittelamerika0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "suedamerika":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/suedamerika0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "naherosten":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/naherosten0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "ostasien":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/ostasien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "suedostasien":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/suedostasien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "zentralasien":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/zentralasien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "australienundozeanien":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/australienundozeanien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

#------------------------------------------------------------------------------------------

	def SatEntryItem(self,entry):
		if (getDesktop(0).size().width() == 1280):
			ItemSkin = 92
		else:
			ItemSkin = 92

		rot = 16711680
		gruen = 0x4ad53b
		dgruen = 0x339229
		tpschwarz = 99000000
		drot = 0xf47d19
		mblau = 8900346
		hblau = 11592447
		dblau = 5215437
		weiss = 0xffffff
		orange = 0xf47d19
		grau = 0x565656
		res = [entry]
		#return (eListboxPythonMultiContent.TYPE_TEXT, pos[0], pos[1], size[0], size[1], font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)
		res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 2), size=(200,92), png=entry[0]))  # png vorn
		res.append(MultiContentEntryText(pos=(240, 27), size=(360, 50), font=0, text=entry[1], color=weiss, color_sel=mblau, backcolor_sel=grau))
		return res

#------------------------------------------------------------------------------------------
# Europe - Maps
# -------------------------------------------------------------------

class SatPanelListd(MenuList):

	if (getDesktop(0).size().width() == 1280):
		ItemSkin = 142
	else:
		ItemSkin = 122

	def __init__(self, list, font0 = 28, font1 = 16, itemHeight = ItemSkin, enableWrapAround = True):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", font0))
		self.l.setFont(1, gFont("Regular", font1))
		self.l.setItemHeight(itemHeight)

# -------------------------------------------------------------------

class SatPaneld(Screen, HelpableScreen):

	def __init__(self, session, ort):
		self.session = session
		self.ort = ort

		if (getDesktop(0).size().width() == 1280):
			self.skin = "<screen name=\"SatPaneld\" position=\"center,center\" size=\"630,500\" title=\"" + _("Europe") + "\" backgroundColor=\"#40000000\">"
			self.skin += """<widget name="Mlist" position="10,25" size="600,430" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""
		else:
			self.skin = "<screen name=\"SatPaneld\" position=\"center,center\" size=\"630,440\" title=\"" + _("Europe") + "\" backgroundColor=\"#40000000\">"
			self.skin += """<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""

		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorAT'), _("Austria"), 'wetterkontorAT')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorBE'), _("Belgium"), 'wetterkontorBE')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorDN'), _("Denmark"), 'wetterkontorDN')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorFR'), _("France"), 'wetterkontorFR')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorDE'), _("Germany"), 'wetterkontorDE')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorGB'), _("Great Britain"), 'wetterkontorGB')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorIE'), _("Ireland"), 'wetterkontorIE')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorIT'), _("Italy"), 'wetterkontorIT')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorLU'), _("Luxembourg"), 'wetterkontorLU')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorNL'), _("Netherlands"), 'wetterkontorNL')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorPO'), _("Portugal"), 'wetterkontorPO')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorES'), _("Spain"), 'wetterkontorES')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorCH'), _("Switzerland"), 'wetterkontorCH')))
                
		self.onChangedEntry = []
		self["Mlist"] = SatPanelListb([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_blue"] = StaticText(_("Settings"))
		self["Title"] = StaticText(_("Europe"))

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, _("Exit - End")),
				"left": (self.left, _("Left - Previous page")),
				"right": (self.right, _("Right - Next page")),
				"up": (self.up, _("Up - Previous")),
				"down": (self.down, _("Down - Next")),
				"blue": (self.PicSetupMenu, _("Blue - Settings")),
				"ok": (self.ok, _("OK - Show")),
			}, -2)

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
		#global menu
		menu = self['Mlist'].l.getCurrentSelection()[0][2]
		##print "Press OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap(resolveFilename(SCOPE_PLUGINS)+"Extensions/Foreca/thumb/" + file + ".png")
		res = (png)
		return res

	def PicSetupMenu(self):
		self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satelitephotos are being loaded .....\n\n                       "))
		#self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=4)

		menu = self['Mlist'].l.getCurrentSelection()[0][2]

		if menu == "wetterkontorDE":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/deutschland0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorAT":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/oesterreich0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorNL":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/niederlande0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorDN":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/daenemark0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorCH":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/schweiz0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorBE":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/belgien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorIT":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/italien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorES":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/spanien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorGB":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/grossbritannien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorFR":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/frankreich0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorIE":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/irland0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorLU":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/luxemburg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorPO":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.de/maps/portugal0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

#------------------------------------------------------------------------------------------

	def SatEntryItem(self,entry):
		if (getDesktop(0).size().width() == 1280):
			ItemSkin = 142
		else:
			ItemSkin = 122

		rot = 16711680
		gruen = 0x4ad53b
		dgruen = 0x339229
		tpschwarz = 99000000
		drot = 0xf47d19
		mblau = 8900346
		hblau = 11592447
		dblau = 5215437
		weiss = 0xffffff
		orange = 0xf47d19
		grau = 0x565656
		res = [entry]
		#return (eListboxPythonMultiContent.TYPE_TEXT, pos[0], pos[1], size[0], size[1], font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)
		res.append(MultiContentEntryPixmapAlphaTest(pos=(2, 5), size=(200,ItemSkin -2), png=entry[0]))  # png vorn
		res.append(MultiContentEntryText(pos=(200, 45), size=(360, 50), font=0, text=entry[1], color=weiss, color_sel=mblau, backcolor_sel=grau))
		return res

#------------------------------------------------------------------------------------------
#-------------------------- Picture viewer for large pictures -----------------------------
#------------------------------------------------------------------------------------------

class PicView(Screen):

	def __init__(self, session, filelist, index, path, startslide):
		self.session = session
		self.bgcolor = "#00000000"
		space = 5
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()

		self.skindir = "/tmp"
		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" > \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\""+ str(size_w) + "," + str(size_h) + "\" backgroundColor=\""+ self.bgcolor +"\" /> \
			<widget name=\"pic\" position=\"" + str(space) + "," + str(space) + "\" size=\"" + str(size_w-(space*2)) + "," + str(size_h-(space*2)) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			</screen>"

		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions", "MenuActions", "SetupActions"],
			{
				"cancel": self.Exit,
			}, -1)

		self["pic"] = Pixmap()
		self.filelist = filelist
		self.old_index = 0
		self.lastindex = index
		self.currPic = []
		self.shownow = True
		self.dirlistcount = 0
		self.index = 0
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.finish_decode)
		self.onLayoutFinish.append(self.setPicloadConf)
		self.startslide = startslide

	def setPicloadConf(self):
		sc = getScale()
		self.picload.setPara([self["pic"].instance.size().width(), self["pic"].instance.size().height(), sc[0], sc[1], 0, 1, self.bgcolor])
		self.start_decode()

	def ShowPicture(self):
		if self.shownow and len(self.currPic):
			self.shownow = False
			self["pic"].instance.setPixmap(self.currPic[0].__deref__())

	def finish_decode(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr != None:
			self.currPic = []
			self.currPic.append(ptr)
			self.ShowPicture()

	def start_decode(self):
		self.picload.startDecode(self.filelist)

	def Exit(self):
		del self.picload
		self.close(self.lastindex + self.dirlistcount)

#------------------------------------------------------------------------------------------

class View_Slideshow(Screen, InfoBarAspectSelection):

	def __init__(self, session, pindex, startslide):

		pindex = 0 
		print "SlideShow is running ......."
		self.textcolor = config.plugins.foreca.textcolor.value
		self.bgcolor = config.plugins.foreca.bgcolor.value
		space = config.plugins.foreca.framesize.value
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()

		self.skindir = "/tmp"
		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\""+ str(size_w) + "," + str(size_h) + "\" backgroundColor=\""+ self.bgcolor +"\" /> \
			<widget name=\"pic\" position=\"" + str(space) + "," + str(space+40) + "\" size=\"" + str(size_w-(space*2)) + "," + str(size_h-(space*2)-40) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget name=\"point\" position=\""+ str(space+5) + "," + str(space+10) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"" + resolveFilename(SCOPE_PLUGINS)+ "Extensions/Foreca/thumb/record.png\" alphatest=\"on\" /> \
			<widget name=\"play_icon\" position=\""+ str(space+25) + "," + str(space+10) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"" + resolveFilename(SCOPE_PLUGINS)+ "Extensions/Foreca/thumb/ico_mp_play.png\"  alphatest=\"on\" /> \
			<widget name=\"file\" position=\""+ str(space+45) + "," + str(space+10) + "\" size=\""+ str(size_w-(space*2)-50) + ",25\" font=\"Regular;20\" halign=\"left\" foregroundColor=\"" + self.textcolor + "\" zPosition=\"2\" noWrap=\"1\" transparent=\"1\" /> \
			</screen>"
		Screen.__init__(self, session)

		InfoBarAspectSelection.__init__(self)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions"],
			{
				"cancel": self.Exit,
				"yellow": self.PlayPause,
				"blue": self.sleepTimer,
				"left": self.prevPic,
				"right": self.nextPic,
			}, -1)
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

		devicepath = config.plugins.foreca.Device.value
		currDir = devicepath
		self.filelist = FileList(currDir, showDirectories = False, matchingPattern = "^.*\.(jpg)", useServiceRef = False)

		for x in self.filelist.getFileList():
			if x[0][1] == False:
				self.picfilelist.append(currDir + x[0][0])
			else:
				self.dirlistcount += 1

		self.maxentry = len(self.picfilelist)-1
		self.pindex = pindex - self.dirlistcount
		if self.pindex < 0:
			self.pindex = 0
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.finish_decode)
		self.slideTimer = eTimer()
		self.slideTimer.callback.append(self.slidePic)
		if self.maxentry >= 0:
			self.onLayoutFinish.append(self.setPicloadConf)
		if startslide == True:
			self.PlayPause();

	def setPicloadConf(self):
		sc = getScale()
		self.picload.setPara([self["pic"].instance.size().width(), self["pic"].instance.size().height(), sc[0], sc[1], 0, int(config.plugins.foreca.resize.value), self.bgcolor])
		self["play_icon"].hide()
		if config.plugins.foreca.infoline.value == False:
			self["file"].hide()
		self.start_decode()

	def ShowPicture(self):
		if self.shownow and len(self.currPic):
			self.shownow = False
			self["file"].setText(self.currPic[0].replace(".jpg",""))
			self.lastindex = self.currPic[1]
			self["pic"].instance.setPixmap(self.currPic[2].__deref__())
			self.currPic = []
			self.next()
			self.start_decode()

	def finish_decode(self, picInfo=""):
		self["point"].hide()
		ptr = self.picload.getData()
		if ptr != None:
			text = ""
			try:
				text = picInfo.split('\n',1)
				text = "(" + str(self.pindex+1) + "/" + str(self.maxentry+1) + ") " + text[0].split('/')[-1]
			except:
				pass
			self.currPic = []
			self.currPic.append(text)
			self.currPic.append(self.pindex)
			self.currPic.append(ptr)
			self.ShowPicture()

	def start_decode(self):
		self.picload.startDecode(self.picfilelist[self.pindex])
		self["point"].show()

	def next(self):
		self.pindex += 1
		if self.pindex > self.maxentry:
			self.pindex = 0

	def prev(self):
		self.pindex -= 1
		if self.pindex < 0:
			self.pindex = self.maxentry

	def slidePic(self):
		print "[Foreca] slide to next Picture index=" + str(self.lastindex)
		if config.plugins.foreca.loop.value==False and self.lastindex == self.maxentry:
			self.PlayPause()
		self.shownow = True
		self.ShowPicture()

	def PlayPause(self):
		if self.slideTimer.isActive():
			self.slideTimer.stop()
			self["play_icon"].hide()
		else:
			self.slideTimer.start(config.plugins.foreca.slidetime.value*1000)
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

	def Exit(self):
		del self.picload
		for file in self.picfilelist:
			try:
				print file
				os.unlink(file)
			except:
				pass
		self.close(self.lastindex + self.dirlistcount)

	def sleepTimer(self):
		from Screens.SleepTimerEdit import SleepTimerEdit
		self.session.open(SleepTimerEdit)

#------------------------------------------------------------------------------------------
#-------------------------------- Foreca Settings -----------------------------------------
#------------------------------------------------------------------------------------------

class PicSetup(Screen):

	skin = "<screen position=\"center,center\" size=\"480,260\" title=\"" + _("SlideShow Settings") + "\" backgroundColor=\"#000000\" >"
	skin +=	"""<widget name="liste" position="5,5" size="470,250" scrollbarMode="showOnDemand" /> 
		<widget source="key_red" render="Label" position="39,215" zPosition="2" size="102,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" /> 
		<widget source="key_green" render="Label" position="159,215" zPosition="2" size="102,40" font="Regular;18" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" /> 
		<ePixmap position="2,225" size="36,25" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" /> 
		<ePixmap position="122,225" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" /> 
		</screen>"""

	def __init__(self, session):
		self.skin = PicSetup.skin
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["Title"] = StaticText(_("SlideShow Settings"))
		self["actions"] = NumberActionMap(["SetupActions", "ColorActions"],
			{
				"ok": self.save,
				"save": self.save,
				"green": self.save,
				"cancel": self.cancel,
				"red": self.cancel,
				"left": self.keyLeft,
				"right": self.keyRight,
				"0": self.keyNumber,
				"1": self.keyNumber,
				"2": self.keyNumber,
				"3": self.keyNumber,
				"4": self.keyNumber,
				"5": self.keyNumber,
				"6": self.keyNumber,
				"7": self.keyNumber,
				"8": self.keyNumber,
				"9": self.keyNumber
			}, -3)
		self.list = []
		self["liste"] = ConfigList(self.list)

		#self.list.append(getConfigListEntry(_("Picture Y moving"), config.plugins.foreca.max_offsety))
		#self.list.append(getConfigListEntry(_("Delete cached Pictures"), config.plugins.foreca.remove))
		#self.list.append(getConfigListEntry(_("Picture Cache"), config.plugins.foreca.Device))
		self.list.append(getConfigListEntry(_("Scaling Mode"), config.plugins.foreca.resize))
		self.list.append(getConfigListEntry(_("Frame size in full view"), config.plugins.foreca.framesize))
		self.list.append(getConfigListEntry(_("Backgroundcolor"), config.plugins.foreca.bgcolor))
		self.list.append(getConfigListEntry(_("Textcolor"), config.plugins.foreca.textcolor))
		self.list.append(getConfigListEntry(_("SlideTime"), config.plugins.foreca.slidetime))
		self.list.append(getConfigListEntry(_("Show Infoline"), config.plugins.foreca.infoline))
		self.list.append(getConfigListEntry(_("Slide picture in loop"), config.plugins.foreca.loop))
		self.list.append(getConfigListEntry(_("City names as labels in the Main screen"), config.plugins.foreca.citylabels))

	def save(self):
		for x in self["liste"].list:
			x[1].save()
		config.save()
		self.close()

	def cancel(self):
		for x in self["liste"].list:
			x[1].cancel()
		self.close(False,self.session)

	def keyLeft(self):
		self["liste"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["liste"].handleKey(KEY_RIGHT)

	def keyNumber(self, number):
		self["liste"].handleKey(KEY_0 + number)

#------------------------------------------------------------------------------------------
#------------------------------------- Main Program ---------------------------------------
#------------------------------------------------------------------------------------------

def start(session, **kwargs):
	session.open(ForecaPreview)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Foreca Weather Forecast"), description=_("Weather forecast for the upcoming 10 days"), icon="foreca_logo.png", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=start)