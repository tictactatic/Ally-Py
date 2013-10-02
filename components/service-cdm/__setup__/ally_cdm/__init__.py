'''
Created on Jul 15, 2011

@package: service CDM
@copyright 2011 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains content delivery manager setup files.
'''

# --------------------------------------------------------------------

NAME = 'Content delivery manager (CDM) service'
GROUP = 'CDM'
VERSION = '1.0'
DESCRIPTION = 'Provides the content delivery manager and support for handling it'
AUTHOR = 'Gabriel Nistor'
AUTHOR_EMAIL = 'gabriel.nistor@sourcefabric.org'
KEYWORDS = ['Ally', 'REST', 'Content', 'manager', 'service']
LONG_DESCRIPTION = '''This component provide the content delivery management, basically the static resources streaming 
since REST is only for models, usually the REST models will have references to static files, like media files and 
the CDM is used for delivery them.'''
TEST_SUITE = '__unit_test__'
CLASSIFIERS = ['Development Status :: 4 - Beta']
INSTALL_REQUIRES = ['ally-http>=1.0']