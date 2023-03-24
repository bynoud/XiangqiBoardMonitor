from distutils.core import setup # Need this to handle modules
import py2exe 
import math # We have to import all modules used in our program


setup(windows=['ZigaHelper.py'],package_dir= { '': '..' })

