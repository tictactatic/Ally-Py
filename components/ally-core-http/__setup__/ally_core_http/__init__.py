'''
Created on Jul 15, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains setup and configuration files for the HTTP REST server.
'''

# --------------------------------------------------------------------

NAME = 'ally core HTTP'
VERSION = '1.0'
DESCRIPTION = 'Provides the HTTP communication support'
UTHOR = 'Gabriel Nistor'
AUTHOR_EMAIL = 'gabriel.nistor@sourcefabric.org'
KEYWORDS = ['Ally', 'REST', 'core', 'http ']
INSTALL_REQUIRES = ['ally-core>=1.0', 'ally-http>=1.0']
LONG_DESCRIPTION = '''This component provides the actual handling for the HTTP [REST] by combining the ally-core and ally-http.'''
TEST_SUITE = '__unit_test__'
CLASSIFIERS = ['Development Status :: 4 - Beta']