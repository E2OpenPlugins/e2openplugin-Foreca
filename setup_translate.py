from __future__ import print_function
# Language extension for distutils Python scripts. Based on this concept:
# http://wiki.maemo.org/Internationalize_a_Python_application
from distutils import cmd
from distutils.command.build import build as _build
from os import listdir, system
from os.path import join, isdir


class build_trans(cmd.Command):
	description = 'Compile .po files into .mo files'

	def initialize_options(self):
		pass

	def finalize_options(self):
		pass

	def run(self):
		s = join('plugin', 'locale')
		for lang in listdir(s):
			lc = join(s, lang, 'LC_MESSAGES')
			if isdir(lc):
				for f in listdir(lc):
					if f.endswith('.po'):
						src = join(lc, f)
						dest = join(lc, f[:-2] + 'mo')
						print("Language compile %s -> %s" % (src, dest))
						if system("msgfmt '%s' -o '%s'" % (src, dest)) != 0:
							raise (Exception, "Failed to compile: " + src)


class build(_build):
	sub_commands = _build.sub_commands + [('build_trans', None)]

	def run(self):
		_build.run(self)


cmdclass = {
	'build': build,
	'build_trans': build_trans,
}
