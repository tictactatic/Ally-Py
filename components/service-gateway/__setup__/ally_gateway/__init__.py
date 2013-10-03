'''
Created on Jul 15, 2011

@package: service gateway
@copyright 2011 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the gateway setup files.
'''

# --------------------------------------------------------------------

NAME = 'gateway service'
GROUP = 'gateway'
VERSION = '1.0'
DESCRIPTION = 'Provides the gateway service'
AUTHOR = 'Gabriel Nistor'
AUTHOR_EMAIL = 'gabriel.nistor@sourcefabric.org'
KEYWORDS = ['Ally', 'REST', 'gateway', 'service']
LONG_DESCRIPTION = '''This component provides the gateway security service.'''
TEST_SUITE = '__unit_test__'
CLASSIFIERS = ['Development Status :: 4 - Beta']
INSTALL_REQUIRES = ['ally-http>=1.0', 'ally-indexing>=1.0']