'''
Created on Jul 15, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains setup and configuration files for the HTTP REST server.
'''


# --------------------------------------------------------------------

NAME = 'ally HTTP mongrel2 server'
VERSION = '1.0'
DESCRIPTION = 'Provides the HTTP mongrel2 server'
AUTHOR = 'Gabriel Nistor'
AUTHOR_EMAIL = 'gabriel.nistor@sourcefabric.org'
KEYWORDS = ['Ally', 'REST', 'HTTP,' 'mongrel2', 'server']
LONG_DESCRIPTION = '''Similar to the asyncore server but provides support for using 
0MQ messaging in order to communicate with Mongrel2 HTTP server.'''
TEST_SUITE = '__unit_test__'
CLASSIFIERS = ['Development Status :: 4 - Beta']
INSTALL_REQUIRES = ['ally-http>=1.0']
# --------------------------------------------------------------------
# The default configurations
