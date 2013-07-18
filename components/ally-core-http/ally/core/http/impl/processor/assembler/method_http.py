'''
Created on May 29, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the HTTP method name.
'''

from ally.api import config
from ally.container.ioc import injected
from ally.core.impl.processor.assembler.base import excludeFrom, InvokerExcluded, \
    RegisterExcluding
from ally.design.processor.attribute import requires, defines
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec import server
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------
    
class Invoker(InvokerExcluded):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    methodHTTP = defines(str, doc='''
    @rtype: string
    The HTTP method name.
    ''')
    # ---------------------------------------------------------------- Required
    method = requires(int)
    
# --------------------------------------------------------------------

@injected
class MethodHTTPHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the HTTP method name.
    '''
    
    mappings = {
                config.GET: server.HTTP_GET,
                config.DELETE: server.HTTP_DELETE,
                config.INSERT: server.HTTP_POST,
                config.UPDATE: server.HTTP_PUT
                }
    # The configuration methods to HTTP methods mapping.
    
    def __init__(self):
        assert isinstance(self.mappings, dict), 'Invalid mappings %s' % self.mappings
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:RegisterExcluding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the HTTP method name.
        '''
        assert isinstance(register, RegisterExcluding), 'Invalid register %s' % register
        if not register.invokers: return
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            invoker.methodHTTP = self.mappings.get(invoker.method)
            if invoker.methodHTTP is None:
                log.error('Cannot use because the method \'%s\' is not a valid HTTP method, at:%s',
                          invoker.method, invoker.location)
                excludeFrom(chain, invoker)
                continue
