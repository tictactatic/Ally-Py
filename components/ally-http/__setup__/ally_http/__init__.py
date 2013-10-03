'''
Created on Jul 15, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains setup and configuration files for the HTTP REST server.
'''

# --------------------------------------------------------------------

NAME = 'ally HTTP'
GROUP = 'ally'
VERSION = '1.0'
DESCRIPTION = 'Provides the HTTP communication support'
AUTHOR = 'Gabriel Nistor'
AUTHOR_EMAIL = 'gabriel.nistor@sourcefabric.org'
KEYWORDS = ['Ally', 'REST', 'http']
LONG_DESCRIPTION = '''Contains HTTP specific handling for requests and also the basic HTTP server based on the python built in server.'''
INSTALL_REQUIRES = ['ally>=1.0']
TEST_SUITE = '__unit_test__'
CLASSIFIERS = ['Development Status :: 4 - Beta']
