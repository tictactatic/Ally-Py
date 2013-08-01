'''
Created on Jan 28, 2013

@package: captcha
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the captcha gateway.
'''

from ..api.gateway import IGatewayCaptchaService
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from collections import Iterable

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Required
    gateways = requires(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The gateways.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(IGatewayCaptchaService, name='gatewayCaptchaService')
class GatewayCaptchaService(IGatewayCaptchaService):
    '''
    Implementation for @see: IGatewayCaptchaService that provides the captcha gateway data.
    '''
    
    assemblyCaptchaGateways = Assembly; wire.entity('assemblyCaptchaGateways')
    # The assembly to be used for generating gateways
    
    def __init__(self):
        assert isinstance(self.assemblyCaptchaGateways, Assembly), \
        'Invalid assembly gateways %s' % self.assemblyCaptchaGateways
        
        self._processing = self.assemblyCaptchaGateways.create(reply=Reply)
         
    def getCaptcha(self):
        '''
        @see: IGatewayCaptchaService.getCaptcha
        '''
        proc = self._processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        chain = Chain(proc)
        chain.process(**proc.fillIn(reply=proc.ctx.reply())).doAll()
        
        reply = chain.arg.reply
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if Reply.gateways not in reply: return ()
        return reply.gateways
                
