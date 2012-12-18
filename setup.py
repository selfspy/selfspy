import os
import platform
if platform.system() == 'Darwin':
    req_file = 'osx-requirements.txt'
else:
    req_file = 'requirements.txt'
with open(os.path.join(os.path.dirname(__file__), req_file)) as f:
    requires = f.readlines()

from setuptools import setup


setup(name="selfspy",
      # version='0.0.0',
      packages=['selfspy'],
      author="David Fendrich",
      # author_email='',
      description=''.join("""
          Log everything you do on the computer, for statistics,
          future reference and all-around fun!
      """.strip().split('\n')),
      install_requires=requires,
      entry_points=dict(console_scripts=['selfspy=selfspy:main',
                                         'selfstats=selfspy.stats:main']))
