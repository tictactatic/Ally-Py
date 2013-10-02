'''
Created on Jul 15, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains setup and configuration files for the HTTP REST server.
'''


# --------------------------------------------------------------------

NAME = 'ally HTTP asyncore server'
VERSION = '1.0'
DESCRIPTION = 'Provides the HTTP asyncore server'
AUTHOR = 'Gabriel Nistor'
AUTHOR_EMAIL = 'gabriel.nistor@sourcefabric.org'
KEYWORDS = ['Ally', 'REST', 'HTTP', 'asyncore', 'server']
LONG_DESCRIPTION = '''Provides an HTTP server substitute for the basic server from ally-http 
that handles the requests in an asyncore manner by using the python built in asyncore package.'''
TEST_SUITE = '__unit_test__'
CLASSIFIERS = ['Development Status :: 4 - Beta']
INSTALL_REQUIRES = ['ally-http>=1.0']
