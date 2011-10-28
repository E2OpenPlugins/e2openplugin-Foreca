# -*- coding: UTF-8 -*-

#-------------------------------------------------------
#
#              Foreca Wetterprognose
#
#   Deze Plugin haalt van Foreca de actuele
#   Weervoorspelling voor de komende 10 dagen op.
#
#
#   We wensen alle gebruikers heerlijk weer toe!
#
#                 Versie 1.6
#
#                  21.10.2011
#
#        Gegevensbron: http://www.foreca.nl
#
#             Ontwerp en idee van
#                  @Bauernbub
#            enigma2 mod door mogli123
#-------------------------------------------------------

from Components.ActionMap import HelpableActionMap
from Components.ActionMap import ActionMap, NumberActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Button import Button
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
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
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, fileExists
from Tools.HardwareInfo import HardwareInfo
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage

import htmlentitydefs, re, urllib2, urllib
from re import sub, split, search, match, findall
import os
from os import system, remove, path, walk, makedirs, listdir
from time import *
import string

config.plugins.foreca = ConfigSubsection()
config.plugins.foreca.Device = ConfigSelection(default="/usr/lib/enigma2/python/Plugins/Extensions/Foreca/bilder/", choices = [("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/", _("...Plugins/Extensions/Foreca/")), ("/media/hdd/Foreca/", _("/media/hdd/Foreca/")), ("/var/swap/Foreca/", _("/var/swap/Foreca/"))])
config.plugins.foreca.resize = ConfigSelection(default="0", choices = [("0", _("simple")), ("1", _("better"))])
config.plugins.foreca.bgcolor = ConfigSelection(default="#00000000", choices = [("#00000000", _("black")),("#009eb9ff", _("blue")),("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.foreca.textcolor = ConfigSelection(default="#0038FF48", choices = [("#00000000", _("black")),("#009eb9ff", _("blue")),("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.foreca.framesize = ConfigInteger(default=5, limits=(5, 99))
config.plugins.foreca.remove = ConfigSelection(default="0", choices = [("0", _("Yes")), ("1", _("No"))])
config.plugins.foreca.slidetime = ConfigInteger(default=1, limits=(1, 60))
config.plugins.foreca.infoline = ConfigEnableDisable(default=True)
config.plugins.foreca.loop = ConfigEnableDisable(default=False)

global MAIN_PAGE
MAIN_PAGE = "http://www.foreca.nl"
PNG_PATH = resolveFilename(SCOPE_PLUGINS)+"/Extensions/Foreca/picon/"
deviceName = HardwareInfo().get_device_name()

# Make Path for Slideshow
if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/bilder") is False:
		os.system("mkdir -p /usr/lib/enigma2/python/Plugins/Extensions/Foreca/bilder")

#---------------------- Skin Funktionen ---------------------------------------------------
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
		tlist.append(("Letterbox", "letterbox"))
		tlist.append(("PanScan", "panscan"))
		tlist.append(("Non Linear", "non"))
		tlist.append(("Bestfit", "bestfit"))
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

#--------------------------- Alle Listeneintraege durchlaufen -----------------------------

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
		self.thumb = "/usr/lib/enigma2/python/Plugins/Extensions/Foreca/thumb/" + str(thumbUrl+ ".png")
		self.wind = "/usr/lib/enigma2/python/Plugins/Extensions/Foreca/thumb/" + str(windlink)
		self.buildEntry(None)

#----------------------------------- Eintrasege fuer Liste bilden ------------------------------------------------

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

		self.temptext = "Temp"
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

		# Zeit
		self.res.append(MultiContentEntryText(pos=(10, 26), size=(70, 24), font=0, text=self.x[1], color=weiss, color_sel=weiss))

		# Temp
		self.res.append(MultiContentEntryText(pos=(215, 13), size=(80, 24), font=0, text="Temp", color=weiss, color_sel=weiss))
		self.res.append(MultiContentEntryText(pos=(207, 39), size=(80, 24), font=1, text=self.x[2], color=self.tempcolor, color_sel=self.tempcolor))
		self.res.append(MultiContentEntryText(pos=(248, 39), size=(80, 24), font=1, text="°C",  color=self.tempcolor, color_sel=self.tempcolor))
                
		# Wind
		self.res.append(MultiContentEntryText(pos=(339, 13), size=(125, 24), font=0, text="Wind", color=weiss, color_sel=weiss))
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

# -------------------------- Menue Liste aufbauen -----------------------------------------

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
#------------------------------ Foreca Programmvorschau---------------------------------------
#------------------------------------------------------------------------------------------

class ForecaPreview(Screen, HelpableScreen):

	def __init__(self, session):
		global MAIN_PAGE, menu
		self.session = session
		MAIN_PAGE = "http://www.foreca.nl"

		# aktuelle, lokale Zeit als Tulpel
		lt = localtime()
		# Entpacken des Tupels, Datum
		jahr, monat, tag = lt[0:3]
		heute ="%04i%02i%02i" % (jahr,monat,tag)
		self.tag = 0

		# Startort einlesen
		global city
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/startservice.cfg"):
			file = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/startservice.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort ="Nederland/Utrecht"
		
		MAIN_PAGE = "http://www.foreca.nl/" + self.ort + "?details=" + heute

		desktop = getDesktop(0)
		size = desktop.size()
		width = size.width()
		print "Desktop ", size, width
		if width == 1024:
			self.skin = """<screen position="center,65" size="899,480" title="Foreca Weersverwachting V 1.6 NL" backgroundColor="#40000000" >"""
			self.skin += """<widget name="MainList" position="0,65" size="899,363" zPosition="3" backgroundColor="#40000000" backgroundColorSelected="#565656" selectionDisabled="1" scrollbarMode="showOnDemand" />
				<widget source="Titel" render="Label" position="120,3" zPosition="3" size="740,40" font="Regular;36" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="Titel2" render="Label" position="288,5" zPosition="2" size="440,40" font="Regular;28" valign="center" halign="left" transparent="1" foregroundColor="#f47d19"/>
				<eLabel position="5,55" zPosition="2" size="870,1" backgroundColor="#FFFFFF" />
				<widget source="key_red" render="Label" position="70,438" zPosition="2" size="200,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_green" render="Label" position="260,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="key_yellow" render="Label" position="450,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="key_blue" render="Label" position="640,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<widget source="key_ok" render="Label" position="730,438" zPosition="2" size="180,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff"/>
				<ePixmap position="27,442" size="36,25" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="217,442" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
				<ePixmap position="407,442" size="36,25" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="597,442" size="36,25" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				<eLabel position="5,437" zPosition="2" size="870,2" backgroundColor="#FFFFFF" />
			</screen>"""
		else:
			self.skin = """<screen position="center,center" size="970,505" title="Foreca Weersverwachting V 1.6 NL" backgroundColor="#40000000" >"""
			self.skin += """<widget name="MainList" position="0,90" size="970,365" zPosition="3" backgroundColor="#40000000" backgroundColorSelected="#565656" selectionDisabled="1" scrollbarMode="showOnDemand" />
				<widget source="Titel" render="Label" position="4,10" zPosition="3" size="968,40" font="Regular;30" valign="center" halign="center" transparent="1" foregroundColor="#ffffff"/>
				<widget source="Titel2" render="Label" position="299,15" zPosition="2" size="440,40" font="Regular;28" valign="center" halign="left" transparent="1" foregroundColor="#f47d19"/>
				<eLabel position="5,70" zPosition="2" size="970,1" backgroundColor="#FFFFFF" />
				<widget source="key_red" render="Label" position="39,463" zPosition="2" size="109,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_green" render="Label" position="184,463" zPosition="2" size="113,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_yellow" render="Label" position="333,463" zPosition="2" size="113,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_blue" render="Label" position="480,463" zPosition="2" size="117,40" font="Regular;20" valign="center" halign="left" transparent="1" foregroundColor="#ffffff" />
				<widget source="key_ok" render="Label" position="598,463" zPosition="2" size="94,40" font="Regular;17" valign="center" halign="center" transparent="1" foregroundColor="#ffffff" />
				<eLabel text="(Menu) Weerkaarten" position="737,463" zPosition="2" size="120,40" font="Regular;17" valign="center" halign="center" transparent="1" foregroundColor="#ffffff" />
				<eLabel text="(info) Legenda" position="883,463" zPosition="2" size="94,40" font="Regular;17" valign="center" halign="center" transparent="1" foregroundColor="#ffffff" />
				<ePixmap position="2,470" size="36,25" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="148,470" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
				<ePixmap position="296,470" size="36,25" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="445,470" size="36,25" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				<eLabel position="5,460" zPosition="2" size="970,2" backgroundColor="#FFFFFF" />
			</screen>"""

		Screen.__init__(self, session)
		self["navigationTitle"] = Label(" ")
		self["MainList"] = MainMenuList()
		self["Titel"] = StaticText()
		self["Titel2"] = StaticText()
		self["Titel2"].text = _("Een ogenblik geduld ...")
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_red"] = StaticText()
		self["key_blue"] = StaticText()
		self["key_ok"] = StaticText()
		self["key_red"].text = _("Week")
		self["key_green"].text = _("Favoriet 1")
		self["key_yellow"].text = _("Favoriet 2")
		self["key_blue"].text = _("Startpagina")
		self["key_ok"].text = _("(OK) Stad")
		#self["info"] = StaticText()
		#self["info"].text = _("(info) Legenda")
		#self["menu"] = StaticText()
		#self["menu"].text = _("(MENU) Kaarten")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.exit, "Exit - Beeindigen"),
				"menu": (self.Menu, "Menu - Weerkaarten"),
				"showEventInfo": (self.info, "Info - Legenda"),
				"ok": (self.OK, "OK - Stad"),
				"left": (self.left, "Links - Pagina verder"),
				"right": (self.right, "Rechts - Pagina terug"),
				"up": (self.up, "Op - Omhoog"),
				"down": (self.down, "Neer - Omlaag"),
				"red": (self.red, "Rood - Weekoverzicht"),
				"green": (self.Fav1, "Groen - Favoriet 1"),
				"yellow": (self.Fav2, "Geel - Favoriet 2"),
				"blue": (self.Fav0, "Blauw - Startpagina"),
				"0": (self.Tag0, "0 - Vandaag"),
				"1": (self.Tag1, "1 - Vandaag + 1 dag"),
				"2": (self.Tag2, "2 - Vandaag + 2 dagen"),
				"3": (self.Tag3, "3 - Vandaag + 3 dagen"),
				"4": (self.Tag4, "4 - Vandaag + 4 dagen"),
				"5": (self.Tag5, "5 - Vandaag + 5 dagen"),
				"6": (self.Tag6, "6 - Vandaag + 6 dagen"),
				"7": (self.Tag7, "7 - Vandaag + 7 dagen"),
				"8": (self.Tag8, "8 - Vandaag + 8 dagen"),
				"9": (self.Tag9, "9 - Vandaag + 9 dagen"),
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

	def StartPage(self):
		self["Titel"].text = _("                                   ")
		self["Titel2"].text = _("Een ogenblik geduld ...")
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
		os.system("rm /tmp/sat.jpg; rm /tmp/sat.html; rm /tmp/meteogram.png")
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
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/startservice.cfg"):
			file = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/startservice.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort ="Nederland/Utrecht"
		self.Zukunft(0)

	def Fav1(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/fav1.cfg"):
			file = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/fav1.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort ="New_York/New_York_City"
		self.Zukunft(0)

	def Fav2(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/fav2.cfg"):
			file = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/fav2.cfg","r")
			self.ort = str(file.readline().strip())
			file.close()
		else:
			self.ort ="Russia/Moskva"
		self.Zukunft(0)

	def Zukunft(self, ztag=0):
		global MAIN_PAGE
		# aktuelle, lokale Zeit als Tupel
		lt = localtime()
		jahr, monat, tag = lt[0:3]

		# Zukunft berechnen
		ntag = tag + ztag
		zukunft = jahr, monat, ntag, 0, 0, 0, 0, 0, 0
		morgen = mktime(zukunft)
		lt = localtime(morgen)
		jahr, monat, tag = lt[0:3]
		morgen ="%04i%02i%02i" % (jahr,monat,tag)

		MAIN_PAGE = "http://www.foreca.nl/" + self.ort + "?details=" + morgen
		##print "Taglink ", MAIN_PAGE

		# im Gui anzeigen
		self.StartPage()

	def OK(self):
		global city
		panelmenu = ""
		city = self.ort
		self.session.openWithCallback(self.OKCallback, CityPanel,panelmenu)

	def info(self):
		message = "%s" % (_("\n0 - 9     =   Prognose over (x) dagen\n\nVOL+/-    =   snel scrollen (Stad keuze)\n\n<   >     =   Prognose komende/vorige dag\n\nInfo     =  deze info\n\nMenu     =  Satellietfoto's en kaarten\n\nRood     =  Temperatuurverloop over de volgende 5 dagen\n\nGroen  =  Ga naar favoriet 1\n\nGeel    =  Ga naar Favoriet 2\n\nBlauw    =  Ga naar Home-Favoriet\n\nWindrichting     =  Icon bijv. Pijl -> wijst naar rechts betekent: Wind waait uit het westen\n"))
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO)

	def OKCallback(self):
		global city
		self.ort = city
		self.Zukunft(0)
		##print "MenuCallback "

	def Menu(self):
		self.session.openWithCallback(self.MenuCallback, SatPanel, self.ort)

	def MenuCallback(self):
		global menu

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

	#def left(self):
	#	if not self.working:
	#		self["MainList"].pageUp()

	#def right(self):
	#	if not self.working:
	#		self["MainList"].pageDown()

	def up(self):
		if not self.working:
			self["MainList"].up()

	def down(self):
		if not self.working:
			self["MainList"].down()

	def red(self):
		if not self.working:
			#self.loc_id = current id
			self.url="http://www.foreca.nl/meteogram.php?loc_id=" + self.loc_id + "&lang=nl&units=metrickmh/meteogram.png"
			self.loadPicture(self.url)

# ----------------------------------------------------------------------

	def getForecaPage(self,html):
		#new Ajax.Request('/lv?id=102772400', {
		fulltext = re.compile(r"new Ajax.Request.+?lv.+?id=(.+?)'", re.DOTALL)
		id = fulltext.findall(html)
		self.loc_id = str(id[0])

		# <!-- START -->
		#<h6><span>Dienstag</span> MÃ¤rz 29</h6>

		##print "[Foreca] Start:" + str(len(html))
		fulltext = re.compile(r'<!-- START -->.+?<h6><span>(.+?)</h6>', re.DOTALL)
		titel = fulltext.findall(html)
		titel[0] = str(sub('<[^>]*>',"",titel[0]))
		#print titel[0]
		#self["Titel"].setText(titel[0])

		# <a href="/Austria/Linz?details=20110330">Mi</a>
		fulltext = re.compile(r'<!-- START -->(.+?)<h6>', re.DOTALL)
		link = str(fulltext.findall(html))
		#print link

		fulltext = re.compile(r'<a href=".+?>(.+?)<.+?', re.DOTALL)
		tag = str(fulltext.findall(link))
		#print "Tag ", tag

		# ---------- Wetterdaten -----------

		# <div class="row clr0">
		fulltext = re.compile(r'<!-- START -->(.+?)<div class="datecopy">', re.DOTALL)
		html = str(fulltext.findall(html))

		##print "zoeken ....."
		list = []

		fulltext = re.compile(r'<a href="(.+?)".+?', re.DOTALL)
		taglink = str(fulltext.findall(html))
		#taglink = konvert_uml(taglink)
		#print "Taglink ", taglink

		fulltext = re.compile(r'<a href=".+?>(.+?)<.+?', re.DOTALL)
		tag = fulltext.findall(html)
		#print "Dag ", str(tag)

		# <div class="c0"> <strong>17:00</strong></div>
		fulltime = re.compile(r'<div class="c0"> <strong>(.+?)<.+?', re.DOTALL)
		zeit = fulltime.findall(html)
		#print "Tijd ", str(zeit)

		#<div class="c4">
		#<span class="warm"><strong>+15&deg;</strong></span><br />
		fulltime = re.compile(r'<div class="c4">.*?<strong>(.+?)&.+?', re.DOTALL)
		temp = fulltime.findall(html)
		#print "Temp ", str(temp)

		# <div class="symbol_50x50d symbol_d000_50x50" title="onbewolkt"
		fulltext = re.compile(r'<div class="symbol_50x50.+? symbol_(.+?)_50x50.+?', re.DOTALL)
		thumbnails = fulltext.findall(html)

		fulltext = re.compile(r'<div class="c3">.+? (.+?)<br />.+?', re.DOTALL)
		titel1 = fulltext.findall(html)
		#print "Titel ", str(titel1).lstrip("\t").lstrip()

		fulltext = re.compile(r'<div class="c3">.+?<br />(.+?)</strong>.+?', re.DOTALL)
		titel2 = fulltext.findall(html)
		#print "Titel ", str(titel2).lstrip("\t").lstrip()

		fulltext = re.compile(r'<div class="c3">.+?</strong><br />(.+?)</.+?', re.DOTALL)
		titel3 = fulltext.findall(html)
		#print "Titel ", str(titel3).lstrip("\t").lstrip()

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
			#Satz1 = titel1[x]
			Satz1 = self.konvert_uml(titel1[x])
			titel2[x] = str(sub('<[^>]*>',"",titel2[x]))
			#Satz2 = titel2[x]
			Satz2 = self.konvert_uml(titel2[x])
			titel3[x] = str(sub('<[^>]*>',"",titel3[x]))
			#Satz3 = titel3[x]
			Satz3 = self.konvert_uml(titel3[x])
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

		self["Titel2"].text = _("                                   ")
		self["Titel"].text = _(self.ort) + "  -  " + titel[0]
		self["MainList"].SetList(list)
		self["MainList"].selectionEnabled(1)
		self["MainList"].show

#------------------------------------------------------------------------------------------
	def konvert_uml(self,Satz):
		return Satz[Satz.rfind("\\t")+2:len(Satz)]	
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
		self.skin = """<screen name="CityPanel" position="center,center" size="730,540" title="Kies een stad" backgroundColor="#40000000">
			<widget name="Mlist" position="10,10" size="700,490" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			<eLabel position="0,515" zPosition="2" size="630,1" backgroundColor="#c1cdc1" />
			<widget source="key_green" render="Label" position="50,512" zPosition="2" size="150,30" font="Regular;20" valign="center" halign="left" transparent="1" />
			<widget source="key_yellow" render="Label" position="200,512" zPosition="2" size="150,30" font="Regular;20" valign="center" halign="left" transparent="1" />
			<widget source="key_blue" render="Label" position="350,514" zPosition="2" size="350,30" font="Regular;20" valign="center" halign="left" transparent="1" />
			<ePixmap position="0,515" size="36,25" pixmap="skin_default/buttons/key_green.png" transparent="1" alphatest="on" />
			<ePixmap position="150,515" size="36,25" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="300,515" size="36,25" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
		</screen>"""

		Screen.__init__(self, session)
		self.Mlist = []

		self.maxidx = 0
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/City.cfg"):
			file = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/City.cfg", "r")
			for line in file:
				text = line.strip()
				self.maxidx += 1
				self.Mlist.append(self.CityEntryItem((_(text), text)))
			file.close

		self.onChangedEntry = []
		self["Mlist"] = CityPanelList([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)

		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["key_green"].text = _("Favoriet 1")
		self["key_yellow"].text = _("Favoriet 2")
		self["key_blue"].text = _("Startpagina")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self,"AAFKeyActions",
			{
				"cancel": (self.Exit, "Exit - Beeindigen"),
				"left": (self.left, "Links - Pagina verder"),
				"right": (self.right, "Rechts - Pagina terug"),
				"up": (self.up, "Op - Omhoog"),
				"down": (self.down, "Neer - Omlaag"),
				"ok": (self.ok, "OK - Kies"),
				"green": (self.green, "Groen - Favoriet 1"),
				"yellow": (self.yellow, "Geel - Favoriet 2"),
				"blue": (self.blue, "Blauw - Startpagina"),
				"nextBouquet": (self.jump500_down, "Kanaal+ - 500 terug"),
				"prevBouquet": (self.jump500_up, "Kanaal- - 500 verder"),
				"volumeDown": (self.jump100_up, "Volume- - 100 verder"),
				"volumeUp": (self.jump100_down, "Volume+ - 100 terug")
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
		##print "druk op OK", city
		self.close()

	def blue(self):
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "[Foreca] Service:", city
		fwrite = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/startservice.cfg", "w")
		fwrite.write(city)
		fwrite.close()
		message = "%s %s" % (_("Deze stad is als Startpagina opgeslagen!\n\n                       "), city)
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=3)

	def green(self):
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "[Foreca] Service:", city
		fwrite = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/fav1.cfg", "w")
		fwrite.write(city)
		fwrite.close()
		message = "%s %s" % (_("Deze stad is als favoriet 1 opgeslagen!\n\n                       "), city)
		self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=3)

	def yellow(self):
		city = self['Mlist'].l.getCurrentSelection()[0][0]
		##print "[Foreca] Service:", city
		fwrite = open("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/fav2.cfg", "w")
		fwrite.write(city)
		fwrite.close()
		message = "%s %s" % (_("Deze stad is als favoriet 2 opgeslagen!\n\n                       "), city)
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
#    Europa Kaarten
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
			self.skin = """<screen name="SatPanel" position="center,center" size="630,500" title="Satellietfoto's" backgroundColor="#40000000">
				<widget name="Mlist" position="10,10" size="600,430" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
				<eLabel position="0,445" zPosition="2" size="630,1" backgroundColor="#c1cdc1" />
				<widget source="key_yellow" render="Label" position="220,450" zPosition="2" size="239,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_blue" render="Label" position="493,450" zPosition="2" size="142,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_red" render="Label" position="52,450" zPosition="2" size="124,45" font="Regular;20" valign="center" halign="left" transparent="1" />
				<ePixmap position="12,460" size="36,20" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="455,460" size="36,20" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
				<ePixmap position="178,460" size="36,20" pixmap="skin_default/buttons/key_yellow.png" transparent="1" alphatest="on" />
			</screen>"""
		else:
			self.skin = """<screen name="SatPanel" position="center,center" size="630,440" title="Satellietfoto's" backgroundColor="#252525">
				<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#252525"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
				<eLabel position="0,385" zPosition="2" size="630,1" backgroundColor="#c1cdc1" />
				<widget source="key_red" render="Label" position="150,397" zPosition="2" size="290,30" font="Regular;20" valign="center" halign="left" transparent="1" />
				<widget source="key_blue" render="Label" position="260,397" zPosition="2" size="290,30" font="Regular;20" valign="center" halign="left" transparent="1" />
				<ePixmap position="90,400" size="36,20" pixmap="skin_default/buttons/key_red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,400" size="36,20" pixmap="skin_default/buttons/key_blue.png" transparent="1" alphatest="on" />
			</screen>"""

		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('satelliet'), _("Weerkaart Video"), 'satelliet')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('neerslag'), _("Buienradar Video"), 'neerslag')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('bewolking'), _("Bewolking Video"), 'bewolking')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('eumetsat'), _("Eumetsat"), 'eumetsat')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('luchtdruk'), _("Luchtdruk"), 'luchtdruk')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('infrarotmetoffice'), _("Infrarood"), 'infrarotmetoffice')))
                
		self.onChangedEntry = []
		self["Mlist"] = SatPanelList([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_red"] = StaticText()
		self["key_red"].text = _("Continenten")
		self["key_green"] = StaticText()
		self["key_green"].text = _("Europa")
		self["key_yellow"] = StaticText()
		self["key_yellow"].text = _("Duitsland")
		self["key_blue"] = StaticText()
		self["key_blue"].text = _("Instellingen")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, "Exit - Beeindigen"),
				"left": (self.left, "Links - Pagina verder"),
				"right": (self.right, "Rechts - Pagina terug"),
				"up": (self.up, "Op - Omhoog"),
				"down": (self.down, "Neer - Omlaag"),
				"red": (self.SatPanelc, "Rood - Continenten"),
				"green": (self.SatPaneld, "Groen - Europa"),
				"yellow": (self.SatPanelb, "Geel - Duitsland"),
				"blue": (self.PicSetupMenu, "Blauw - Instellingen"),
				"ok": (self.ok, "OK - Toon"),
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
		##print "druk op OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/thumb/" + file + ".png")
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

		#message = "%s" % (_("Satellietfoto's worden geladen .....\n\n                       "))
		#self.session.open( MessageBox, message, MessageBox.TYPE_INFO, timeout=4)

		menu = self['Mlist'].l.getCurrentSelection()[0][2]
		if menu == "satelliet":
			# http://www.foreca.de/Austria/Linz?map=sat
			devicepath = "/tmp/sat.html"
			url = "http://www.foreca.nl/" + self.ort + "?map=sat"

#------------------------------------------------------------------------------------------

		if menu == "neerslag":
			devicepath = "/tmp/sat.html"
			url = "http://www.foreca.nl/" + self.ort + "?map=rain"

#------------------------------------------------------------------------------------------

		if menu == "bewolking":
			devicepath = "/tmp/sat.html"
			url = "http://www.foreca.nl/" + self.ort + "?map=cloud"

#------------------------------------------------------------------------------------------

		if menu == "luchtdruk":
			devicepath = "/tmp/sat.html"
			url = "http://www.foreca.at/" + self.ort + "?map=pressure"

#------------------------------------------------------------------------------------------

		if menu == "satelliet" or menu == "neerslag" or menu == "bewolking" or menu == "luchtdruk":
			# Lade Kategorie Seite und suche BildLink
			h = urllib.urlretrieve(url, devicepath)
			fd=open(devicepath)
			html=fd.read()
			fd.close()

			fulltext = re.compile(r'http://cache-(.+?) ', re.DOTALL)
			PressureLink = fulltext.findall(html)
			PicLink = PressureLink[0]
			PicLink = "http://cache-" +	PicLink

			# Lade Bilder fuer Slideshow
			devicepath = "/usr/lib/enigma2/python/Plugins/Extensions/Foreca/bilder/sat"
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
				file2 = file[2:4]+"-"+file[0:2]+" - "+file[4:6]+" uur"
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
			self.skin = """<screen name="SatPanelb" position="center,center" size="630,500" title="Duitsland" backgroundColor="#40000000">
				<widget name="Mlist" position="10,25" size="600,430" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""
		else:
			self.skin = """<screen name="SatPanelb" position="center,center" size="630,440" title="Satelietfoto's" backgroundColor="#40000000">
				<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""


		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('badenwuerttemberg'), _("Baden-Wuerttemberg"), 'badenwuerttemberg')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('bayern'), _("Bayern"), 'bayern')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('berlin'), _("Berlin"), 'berlin')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('brandenburg'), _("Brandenburg"), 'brandenburg')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('bremen'), _("Bremen"), 'bremen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('hamburg'), _("Hamburg"), 'hamburg')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('hessen'), _("Hessen"), 'hessen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('mecklenburgvorpommern'), _("Mecklenburg-Vorpommern"), 'mecklenburgvorpommern')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('niedersachsen'), _("Niedersachsen"), 'niedersachsen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('nordrheinwestfalen'), _("Nordrhein-Westfalen"), 'nordrheinwestfalen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('rheinlandpfalz'), _("Rheinland-Pfalz"), 'rheinlandpfalz')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('saarland'), _("Saarland"), 'saarland')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('sachsen'), _("Sachsen"), 'sachsen')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('sachsenanhalt'), _("Sachsen-Anhalt"), 'sachsenanhalt')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('schleswigholstein'), _("Schleswig-Holstein"), 'schleswigholstein')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('thueringen'), _("Thueringen"), 'thueringen')))

		self.onChangedEntry = []
		self["Mlist"] = SatPanelListb([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_blue"] = StaticText()
		self["key_blue"].text = _("Instellingen")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, "Exit - Beeindigen"),
				"left": (self.left, "Links - Pagina verder"),
				"right": (self.right, "Rechts - Pagina terug"),
				"up": (self.up, "Op - Omhoog"),
				"down": (self.down, "Neer - Omlaag"),
				"blue": (self.PicSetupMenu, "Blauw - Instellingen"),
				"ok": (self.ok, "OK - Toon"),
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
		##print "druecke OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/bundesland/" + file + ".png")
		res = (png)
		return res

	def PicSetupMenu(self):
		self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satelietfoto's worden geladen .....\n\n                       "))
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
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/bayern0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "berlin":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/berlin0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "brandenburg":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/brandenburg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "bremen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/bremen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "hamburg":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/hamburg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "hessen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/hessen0.jpg", devicepath)
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
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/nordrheinwestfalen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "rheinlandpfalz":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/rheinlandpfalz0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "saarland":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/saarland0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "sachsen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/sachsen0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "sachsenanhalt":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/sachsenanhalt0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "schleswigholstein":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/schleswigholstein0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "thueringen":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/thueringen0.jpg", devicepath)
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
# Weltkarte - Kontinente
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
			self.skin = """<screen name="SatPanelc" position="center,center" size="630,500" title="Wereldkaart - Continenten" backgroundColor="#40000000">
				<widget name="Mlist" position="1,20" size="627,460" zPosition="3" backgroundColor="#40000000" backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""                                  
		else:
			self.skin = """<screen name="SatPanelc" position="center,center" size="630,440" title="Wereldkaart - Continenten" backgroundColor="#252525">
				<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#252525"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
		</screen>"""


		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('europa'), _("Europa"), 'europa')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('afrika-nord'), _("Noord Afrika"), 'afrika-nord')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('afrika-sued'), _("Zuid Afrika"), 'afrika-sued')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('nordamerika'), _("Noord Amerika"), 'nordamerika')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('mittelamerika'), _("Midden Amerika"), 'mittelamerika')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('suedamerika'), _("Zuid Amerika"), 'suedamerika')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('naherosten'), _("Midden Oosten"), 'naherosten')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('ostasien'), _("Oost Azie"), 'ostasien')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('suedostasien'), _("Zuidoost Azie"), 'suedostasien')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('zentralasien'), _("Midden Azie"), 'zentralasien')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('australienundozeanien'), _("Australie"), 'australienundozeanien')))
                
		self.onChangedEntry = []
		self["Mlist"] = SatPanelListc([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		#self["key_blue"] = StaticText()
		#self["key_blue"].text = _("Einstellungen")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, "Exit - Beeindigen"),
				"left": (self.left, "Links - Pagina verder"),
				"right": (self.right, "Rechts - Pagina terug"),
				"up": (self.up, "Op - Omhoog"),
				"down": (self.down, "Neer - Omlaag"),
				#"blue": (self.PicSetupMenu, "Blauw - Instellingen"),
				"ok": (self.ok, "OK - Toon"),
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
		##print "druk op OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/kontinent/" + file + ".png")
		res = (png)
		return res

	#def PicSetupMenu(self):
		#self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satelietfoto's worden geladen .....\n\n                       "))
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
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/afrika_nord0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "afrika-sued":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/afrika_sued0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)
                        
		if menu == "nordamerika":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/nordamerika0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "mittelamerika":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/mittelamerika0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "suedamerika":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/suedamerika0.jpg", devicepath)
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
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/suedostasien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "zentralasien":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/zentralasien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "australienundozeanien":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/australienundozeanien0.jpg", devicepath)
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
# Europa - Kaarten
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
			self.skin = """<screen name="SatPaneld" position="center,center" size="630,500" title="Europa" backgroundColor="#40000000">
				<widget name="Mlist" position="10,25" size="600,430" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""
		else:
			self.skin = """<screen name="SatPaneld" position="center,center" size="630,440" title="Europa" backgroundColor="#40000000">
				<widget name="Mlist" position="10,10" size="600,370" zPosition="3" backgroundColor="#40000000"  backgroundColorSelected="#565656" scrollbarMode="showOnDemand" />
			</screen>"""

		Screen.__init__(self, session)
		self.Mlist = []

		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorBE'), _("Belgie"), 'wetterkontorBE')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorDN'), _("Denemarken"), 'wetterkontorDN')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorDE'), _("Duitsland"), 'wetterkontorDE')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorFR'), _("Frankrijk"), 'wetterkontorFR')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorGB'), _("Groot Brittannie"), 'wetterkontorGB')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorIE'), _("Ierland"), 'wetterkontorIE')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorIT'), _("Italie"), 'wetterkontorIT')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorLU'), _("Luxemburg"), 'wetterkontorLU')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorNL'), _("Nederland"), 'wetterkontorNL')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorAT'), _("Oostenrijk"), 'wetterkontorAT')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorPO'), _("Portugal"), 'wetterkontorPO')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorES'), _("Spanje"), 'wetterkontorES')))
		self.Mlist.append(self.SatEntryItem((self.SatEntryComponent('wetterkontorCH'), _("Zwitserland"), 'wetterkontorCH')))
                
		self.onChangedEntry = []
		self["Mlist"] = SatPanelListb([])
		self["Mlist"].l.setList(self.Mlist)
		self["Mlist"].selectionEnabled(1)
		self["key_blue"] = StaticText()
		self["key_blue"].text = _("Instellingen")

		HelpableScreen.__init__(self)
		self["actions"] = HelpableActionMap(self, "AAFKeyActions",
			{
				"cancel": (self.Exit, "Exit - Beeindigen"),
				"left": (self.left, "Links - Pagina verder"),
				"right": (self.right, "Rechts - Pagina terug"),
				"up": (self.up, "Op - Omhoog"),
				"down": (self.down, "Neer - Omlaag"),
				"blue": (self.PicSetupMenu, "Blauw - Instellingen"),
				"ok": (self.ok, "OK - Toon"),
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
		##print "druecke OK", menu
		#self.close()
		self.SatBild()

	def SatEntryComponent(self,file):
		png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Foreca/thumb/" + file + ".png")
		res = (png)
		return res

	def PicSetupMenu(self):
		self.session.open(PicSetup)

#------------------------------------------------------------------------------------------

	def SatBild(self):

		#message = "%s" % (_("Satelietfoto's worden geladen .....\n\n                       "))
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
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/oesterreich0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorNL":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/niederlande0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorDN":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/daenemark0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorCH":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/schweiz0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorBE":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/belgien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorIT":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/italien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorES":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/spanien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorGB":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/grossbritannien0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorFR":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/frankreich0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorIE":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/irland0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorLU":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/luxemburg0.jpg", devicepath)
			filelist = devicepath
			self.session.open(PicView, filelist, 0, path, False)

		if menu == "wetterkontorPO":
			devicepath = "/tmp/meteogram.png"
			path = "/tmp"
			h = urllib.urlretrieve("http://www.wetterkontor.at/maps/portugal0.jpg", devicepath)
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
#-------------------------- Bildbetrachter der Grossbilder --------------------------------
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
			<eLabel position=\"0,0\" zPosition=\"0\" size=\""+ str(size_w) + "," + str(size_h) + "\" backgroundColor=\""+ self.bgcolor +"\" /><widget name=\"pic\" position=\"" + str(space) + "," + str(space) + "\" size=\"" + str(size_w-(space*2)) + "," + str(size_h-(space*2)) + "\" zPosition=\"1\" alphatest=\"on\" /></screen>"

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
			<eLabel position=\"0,0\" zPosition=\"0\" size=\""+ str(size_w) + "," + str(size_h) + "\" backgroundColor=\""+ self.bgcolor +"\" /><widget name=\"pic\" position=\"" + str(space) + "," + str(space+40) + "\" size=\"" + str(size_w-(space*2)) + "," + str(size_h-(space*2)-40) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget name=\"point\" position=\""+ str(space+5) + "," + str(space+10) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/Foreca/thumb/record.png\" alphatest=\"on\" /> \
			<widget name=\"play_icon\" position=\""+ str(space+25) + "," + str(space+10) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/Foreca/thumb/ico_mp_play.png\"  alphatest=\"on\" /> \
			<widget name=\"file\" position=\""+ str(space+45) + "," + str(space+10) + "\" size=\""+ str(size_w-(space*2)-50) + ",25\" font=\"Regular;20\" halign=\"left\" foregroundColor=\"" + self.textcolor + "\" zPosition=\"2\" noWrap=\"1\" transparent=\"1\" /></screen>"
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
		self["file"] = Label(_("Een ogenblik geduld, foto wordt geladen..."))
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

	skin = """<screen position="center,center" size="480,260" title="Foreca SlideShow Settings" backgroundColor="#000000" >
		<widget name="liste" position="5,5" size="470,250" scrollbarMode="showOnDemand" />
		<eLabel backgroundColor="red" position="28,250" size="140,3" zPosition="2"/>
		<eLabel backgroundColor="green" position="228,250" size="140,3" zPosition="2"/>
		<widget name="key_red" position="28,218" zPosition="3" size="140,40" font="Regular;19" valign="center" halign="center" transparent="1" />
		<widget name="key_green" position="228,218" zPosition="3" size="140,40" font="Regular;19" valign="center" halign="center" transparent="1" />
	</screen>"""

	def __init__(self, session):
		self.skin = PicSetup.skin
		Screen.__init__(self, session)
		self["key_red"] = Button(_("Back"))
		self["key_green"] = Button(_("Save"))
		self["actions"] = NumberActionMap(["SetupActions", "ColorActions"],
			{
				"ok": self.save,
				"green": self.save,
				"cancel": self.close,
				"red": self.close,
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

	def save(self):
		for x in self["liste"].list:
			x[1].save()
		config.save()
		self.close()

	def keyLeft(self):
		self["liste"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["liste"].handleKey(KEY_RIGHT)

	def keyNumber(self, number):
		self["liste"].handleKey(KEY_0 + number)

#------------------------------------------------------------------------------------------
#------------------------------------- Haupt Programm -------------------------------------
#------------------------------------------------------------------------------------------

def start(session, **kwargs):
	session.open(ForecaPreview)

def Plugins(**kwargs):
	return PluginDescriptor(name="Foreca Weersverwachting", description="Weersverwachting 10 dagen", icon="foreca_logo.png", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=start)