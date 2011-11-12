from distutils.core import setup, Extension

pkg = 'Extensions.Foreca'
setup (name = 'enigma2-plugin-extensions-foreca',
       version = '2.0',
       description = 'Foreca - Weather forecast',
       packages = [pkg],
       package_dir = {pkg: 'plugin'},
       package_data = {pkg: ['*.png', '*.xml', '*/*.png']},
       data_files = [('/etc/enigma2/Foreca', ['plugin/City.cfg', 'plugin/Filter.cfg'])]
      )
