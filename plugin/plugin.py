# for localized messages
from . import _

# Plugin definition
from Plugins.Plugin import PluginDescriptor

def main(session, **kwargs):
	global PICON_PATH
	import ui
	ui.PICON_PATH = PICON_PATH
	session.open(ui.ForecaPreview)

def Plugins(path, **kwargs):
	global PICON_PATH
	PICON_PATH = path + "/picon/"
	return PluginDescriptor(name=_("Foreca Weather Forecast"),
		description=_("Weather forecast for the upcoming 10 days"),
		icon="foreca_logo.png",
		where=[PluginDescriptor.WHERE_EXTENSIONSMENU,PluginDescriptor.WHERE_PLUGINMENU],
		fnc=main)
