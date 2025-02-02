from distutils.core import setup
import setup_translate

pkg = 'Extensions.Foreca'
setup(name='enigma2-plugin-extensions-foreca',
      version='3.3.5',
      description='Weather forecast for the upcoming 10 days',
      packages=[pkg],
      package_dir={pkg: 'plugin'},
      package_data={pkg: ['*.png', '*.txt', '*.xml', '*/*.png', '*/*.txt', 'locale/*/LC_MESSAGES/*.mo']},
      data_files=[('/etc/enigma2/Foreca', ['plugin/City.cfg', 'plugin/Filter.cfg'])],
      cmdclass=setup_translate.cmdclass,  # for translation
      )