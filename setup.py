#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup


NAME = 'OASYS1-WISEr'
VERSION = '1.0.2'
ISRELEASED = True

DESCRIPTION = 'WISEr in Python'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Michele Manfredda, Lorenzo Raimondi, Luca Rebuffi'
AUTHOR_EMAIL = 'luca.rebuffi@elettra.eu'
URL = 'https://github.com/oasys-elettra-kit/WISE2'
DOWNLOAD_URL = 'https://github.com/oasys-elettra-kit/WISE2'
LICENSE = 'GPLv3'

KEYWORDS = (
    'waveoptics',
    'simulator',
    'oasys1',
)

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'setuptools',
    'oasys1>=1.0.18',
    'wiselib2',
    'wofry>=1.0.12',
    'wofrywise2'
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.wise2.widgets.light_sources":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.wise2.widgets.optical_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.wise2.widgets.tools":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.wise2.widgets.wofry":["icons/*.png", "icons/*.jpg"],
}

NAMESPACE_PACAKGES = ["orangecontrib", "orangecontrib.wise2", "orangecontrib.wise2.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("wise = orangecontrib.wise", ),
    'oasys.widgets' : (
        "WISEr Light Sources = orangecontrib.wise2.widgets.light_sources",
        "WISEr Optical Elements = orangecontrib.wise2.widgets.optical_elements",
        "WISEr Tools = orangecontrib.wise2.widgets.tools",
        "WISEr Wofry = orangecontrib.wise2.widgets.wofry",
    ),
    'oasys.menus' : ("wisemenu = orangecontrib.wise2.menu",)
}

if __name__ == '__main__':
    is_beta = False

    try:
        import PyMca5, PyQt4

        is_beta = True
    except:
        setup(
              name = NAME,
              version = VERSION,
              description = DESCRIPTION,
              long_description = LONG_DESCRIPTION,
              author = AUTHOR,
              author_email = AUTHOR_EMAIL,
              url = URL,
              download_url = DOWNLOAD_URL,
              license = LICENSE,
              keywords = KEYWORDS,
              classifiers = CLASSIFIERS,
              packages = PACKAGES,
              package_data = PACKAGE_DATA,
              #          py_modules = PY_MODULES,
              setup_requires = SETUP_REQUIRES,
              install_requires = INSTALL_REQUIRES,
              #extras_require = EXTRAS_REQUIRE,
              #dependency_links = DEPENDENCY_LINKS,
              entry_points = ENTRY_POINTS,
              namespace_packages=NAMESPACE_PACAKGES,
              include_package_data = True,
              zip_safe = False,
              )

    if is_beta: raise NotImplementedError("This version of WISE 2 doesn't work with Oasys1 beta.\nPlease install OASYS1 final release: http://www.elettra.eu/oasys.html")
