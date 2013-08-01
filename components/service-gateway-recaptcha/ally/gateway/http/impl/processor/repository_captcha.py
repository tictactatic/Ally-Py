'''
Created on Jun 7, 2013

@package: gateway service reCAPTCHA
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway reCAPTCHA repository processor.
'''

from .respository import GatewayRepositoryHandler, Identifier
from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context

# --------------------------------------------------------------------

class Gateway(Context):
    '''
    The gateway context.
    '''
    # ---------------------------------------------------------------- Defined
    isWithCaptcha = defines(bool, doc='''
    @rtype: boolean
    If True it means the gateway needs to be solved with captcha.
    ''')
    
# --------------------------------------------------------------------

@injected
class GatewayCaptchaRepositoryHandler(GatewayRepositoryHandler):
    '''
    Extension for @see: GatewayRepositoryHandler that provides the service for captcha gateways.
    '''
    
    def process(self, processing, Gateway:Gateway, **keyargs):
        '''
        @see: GatewayRepositoryHandler.process
        '''
        super().process(processing, Gateway=Gateway, **keyargs)
    
    def populate(self, identifier, obj):
        '''
        @see: GatewayCaptchaRepositoryHandler.populate
        
        Provides the captcha mark.
        '''
        assert isinstance(identifier, Identifier), 'Invalid identifier %s' % identifier
        assert isinstance(identifier.gateway, Gateway), 'Invalid gateway %s' % identifier.gateway
        identifier.gateway.isWithCaptcha = True
        return super().populate(identifier, obj)
