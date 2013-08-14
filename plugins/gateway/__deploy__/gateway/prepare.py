'''
Created on Nov 7, 2012

@package: gateway
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Special module that is used in preparing the application deploy.
'''

from ..ally.prepare import OptionsCore, prepareCoreOptions, \
    prepareCoreActions
from ally.container import ioc
from argparse import ArgumentParser
from inspect import isclass
import application

# --------------------------------------------------------------------

class OptionsGateway(OptionsCore):
    '''
    The prepared option class.
    '''
    
    def __init__(self):
        super().__init__()
        self._addIPs = None
        self._remIPs = None
    
    def setAddIPs(self, value):
        '''Setter for adding full access IPs'''
        self._addIPs = value
        self._start = False
        
    def setRemIPs(self, value):
        '''Setter for removing full access IPs'''
        self._remIPs = value
        self._start = False
    
    addIPs = property(lambda self: self._addIPs, setAddIPs)
    remIPs = property(lambda self: self._remIPs, setRemIPs)

# --------------------------------------------------------------------

@ioc.after(prepareCoreOptions)
def prepareGatewayOptions():
    assert isclass(application.Options), 'Invalid options class %s' % application.Options
    class Options(OptionsGateway, application.Options): pass
    application.Options = Options


@ioc.after(prepareCoreActions)
def prepareMongrel2Actions():
    assert isinstance(application.parser, ArgumentParser), 'Invalid parser %s' % application.parser
    application.parser.add_argument('-add-access', metavar='IP', dest='addIPs', nargs='+', default=False,
                                    help='Provide this option to add a full access IPs, all calls from this IP will not be '
                                    'blocked by the gateway, the IPs can be provided as: 127.0.0.1 or 127.*.*.*')
    application.parser.add_argument('-rem-access', metavar='IP', dest='remIPs', nargs='+', default=False,
                                    help='Provide this option to remove full access IPs, the IPs need to be provided exactly '
                                    'with the same form (127.0.0.1 or 127.*.*.*) as they have been added')
