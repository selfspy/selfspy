import os
import platform

# dep_link = []
if platform.system() == 'Darwin':
    req_file = 'osx-requirements.txt'
elif platform.system() == "Windows":
    req_file = "win-requirements.txt"
else:
    req_file = 'requirements.txt'
    #dep_link = ['http://python-xlib.svn.sourceforge.net/viewvc/python-xlib/tags/xlib_0_15rc1/?view=tar#egg=pyxlib']

with open(os.path.join(os.path.dirname(__file__), req_file)) as f:
    requires = list(f.readlines())

print '"%s"' % requires

from setuptools import setup

setup(name="selfspy",
      version='0.3.0',
      packages=['selfspy'],
      author="David Fendrich",
      # author_email='',
      description=''.join("""
          Log everything you do on the computer, for statistics,
          future reference and all-around fun!
      """.strip().split('\n')),
      install_requires=requires,
      #dependency_links=dep_link,
      entry_points=dict(console_scripts=['selfspy=selfspy:main',
                                         'selfstats=selfspy.stats:main']))
