from __future__ import absolute_import
# for localized messages
from . import _

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Configuration
from Components.config import *
config.plugins.foreca = ConfigSubsection()
config.plugins.foreca.extmenu = ConfigEnableDisable(default=True)

def main(session, **kwargs):
	global PICON_PATH
	from . import ui
	ui.PICON_PATH = PICON_PATH
	session.open(ui.ForecaPreview)

def Plugins(path, **kwargs):
	global PICON_PATH
	PICON_PATH = path + "/picon/"
	list = [PluginDescriptor(name=_("Foreca Weather Forecast"),
		description=_("Weather forecast for the upcoming 10 days"),
		icon="foreca_logo.png",
		where=PluginDescriptor.WHERE_PLUGINMENU,
		fnc=main)]
	if config.plugins.foreca.extmenu.value:
		list.append(PluginDescriptor(name=_("Foreca Weather Forecast"),
		description=_("Weather forecast for the upcoming 10 days"),
		icon="foreca_logo.png",
		where=PluginDescriptor.WHERE_EXTENSIONSMENU,
		fnc=main))
	return list
