from . import _

from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Plugins.Plugin import PluginDescriptor

config.plugins.foreca = ConfigSubsection()
config.plugins.foreca.extmenu = ConfigEnableDisable(default=True)


def main(session, **kwargs):
	global PICON_PATH
	from .ui import ForecaPreview
	session.open(ForecaPreview)


def Plugins(path, **kwargs):
	global PICON_PATH
	PICON_PATH = path + "/picon/"
	list = [PluginDescriptor(
			name=_("Foreca Weather Forecast"),
			description=_("Weather forecast for the upcoming 10 days"),
			icon="foreca_logo.png",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main)]
	if config.plugins.foreca.extmenu.value:
		list.append(PluginDescriptor(
					name=_("Foreca Weather Forecast"),
					description=_("Weather forecast for the upcoming 10 days"),
					icon="foreca_logo.png",
					where=PluginDescriptor.WHERE_EXTENSIONSMENU,
					fnc=main))
	return list
