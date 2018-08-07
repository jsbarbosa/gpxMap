import os
import gpxMap
from setuptools import setup

#def read(fname):
#    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "gpxMap",
    version = gpxMap.__version__,
    author = "Juan Barbosa",
    author_email = "js.barbosa10@uniandes.edu.co",
    description = ('Animate GPS data. Use and gpx file to display your GPS data.'),
    license = "GPL",
    keywords = "example documentation tutorial",
    url = "https://github.com/jsbarbosa/gpxMap",
    packages=['gpxMap'],
    install_requires = ['matplotlib', 'gpxpy', 'pillow'],
    long_description = "",#read('README.md'),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
)
