# -*- coding: utf-8 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import gettext, dgettext, bindtextdomain

PluginLanguageDomain = "Foreca"
PluginLanguagePath = "Extensions/Foreca/locale"


def localeInit():
    bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    t = dgettext(PluginLanguageDomain, txt)
    if t == txt:
        #print "[%s] fallback to default translation for %s" %(PluginLanguageDomain, txt)
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)
