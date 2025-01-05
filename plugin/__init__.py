# -*- coding: utf-8 -*-

from __future__ import absolute_import
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os


PluginLanguageDomain = 'Foreca'
PluginLanguagePath = 'Extensions/Foreca/locale'


isDreambox = False
if os.path.exists("/usr/bin/apt-get"):
	isDreambox = True


def localeInit():
	if isDreambox:
		lang = language.getLanguage()[:2]
		os.environ["LANGUAGE"] = lang
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


if isDreambox:
	def _(txt):
		return gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
else:
	def _(txt):
		translated = gettext.dgettext(PluginLanguageDomain, txt)
		if translated:
			return translated
		else:
			print(("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt)))
			return gettext.gettext(txt)

localeInit()
language.addCallback(localeInit)
# URL del file remoto che contiene la nuova base URL
file_url = "https://raw.githubusercontent.com/Belfagor2005/e2openplugin-Foreca/refs/heads/master/plugin/foreca_v.txt"
