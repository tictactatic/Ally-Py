'''
Created on Oct 2, 2013

@package: ally distribution
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for general resources.
'''

from .request_api import external_host, external_port
from .service import packager, path_components
from ally.container import event, support
from ally.support.util_deploy import Options, PREPARE, DEPLOY
from argparse import ArgumentParser
import distribution
import logging

# --------------------------------------------------------------------

logging.basicConfig(format='%(asctime)s %(levelname)-7s %(message)s')
logging.getLogger('ally.distribution').setLevel(logging.INFO)

FLAG_PACKAGE = 'package'
# Flag indicating the packaging action.

# --------------------------------------------------------------------

@event.on(PREPARE)
def prepare():
    assert isinstance(distribution.parser, ArgumentParser), 'Invalid distribution parser %s' % distribution.parser
    assert isinstance(distribution.options, Options), 'Invalid distribution options %s' % distribution.options
    
    distribution.options.location = None
    distribution.options.host = None
    distribution.options.port = None
    
    distribution.options.registerFlagTrue(FLAG_PACKAGE)
    distribution.parser.add_argument('--location', metavar='folder', dest='location', help='The location where '
                                     'the distribution results should be placed, if none provided it will default to '
                                     'a location based on the performed action.')
    distribution.parser.add_argument('--host', dest='host', help='The host from where to fetch API data, this is used '
                                     'only for services that require API data from a deployed application, if not specified '
                                     'it will default to "localhost".')
    distribution.parser.add_argument('--port', dest='port', type=int, help='The port to use with the host, if not specified '
                                     'it will default to "8080".')

@event.on(DEPLOY)
def deploy():
    host = getattr(distribution.options, 'host', None)
    if host: support.force(external_host, host)
    port = getattr(distribution.options, 'port', None)
    if port: support.force(external_port, port)
    if distribution.options.isFlag(FLAG_PACKAGE):
        location = getattr(distribution.options, 'location', None)
        if location: support.force(path_components, location)
        packager().generateSetupFiles()
