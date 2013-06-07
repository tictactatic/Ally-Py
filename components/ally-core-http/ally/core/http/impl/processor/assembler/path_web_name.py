'''
Created on May 29, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the web name for the path.
'''

from ally.api.operator.container import Call
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
import logging
import re

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    hintsCall = definesIf(dict)
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list)
    # ---------------------------------------------------------------- Required
    call = requires(Call)
    location = requires(str)
    
class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    
# --------------------------------------------------------------------

@injected
class PathWebNameHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the web name for path.
    '''
    
    hintName = 'webName'
    # The hint name for the call web name.
    hintDescription = '(string) The name for locating the call, simply put this is the last '\
    'name used in the resource path in order to identify the call.'
    # The hint description.
    
    def __init__(self):
        assert isinstance(self.hintName, str), 'Invalid hint name %s' % self.hintName
        assert isinstance(self.hintDescription, str), 'Invalid hint description %s' % self.hintDescription
        super().__init__(Invoker=Invoker, Element=Element)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the domain based on elements models.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if Register.hintsCall in register:
            if register.hintsCall is None: register.hintsCall = {}
            register.hintsCall[self.hintName] = self.hintDescription
        
        if not register.invokers: return
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.call: continue  # No call to process hints on.
            if not invoker.path: continue  # No path to append the web name to.
            assert isinstance(invoker.call, Call), 'Invalid call %s' % invoker.call
            
            if self.hintName in invoker.call.hints:
                webName = invoker.call.hints[self.hintName]
                assert isinstance(webName, str) and re.match('\w+$', webName), \
                'Invalid web name \'%s\' can only contain alpha numeric characters at:%s' % (webName, invoker.location)
                for el in reversed(invoker.path):
                    assert isinstance(el, Element), 'Invalid element %s' % el
                    if el.name:
                        el.name = '%s%s' % (webName, el.name)
                        break
                else: log.warn('Could not process the web name at:%s', invoker.location)
