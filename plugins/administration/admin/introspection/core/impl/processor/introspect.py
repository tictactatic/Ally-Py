'''
Created on Oct 1, 2013

@package: administration
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that simply provides the introspection solved on the registry.
'''

from ally.design.processor.attribute import attribute
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.design.processor.resolvers import solve
from ally.design.processor.spec import ContextMetaClass

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    introspect = attribute(Context, doc='''
    @rtype: Context
    The introspect context for the registry.
    ''')
      
# --------------------------------------------------------------------

class IntrospectHandler(HandlerProcessor):
    '''
    Provides the introspection solved on the registry or creates one to be solved.
    '''
    
    def __init__(self):
        super().__init__()
    
    def process(self, chain, register:Register, Introspect:Context, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the introspection context.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(Introspect, ContextMetaClass), 'Invalid introspect class %s' % Introspect
       
        if register.introspect is None:
            register.introspect = Introspect()
            solve = True
        else: solve = False
            
        chain.process(introspect=register.introspect)
        
        if not solve: return chain.cancel()  # No need to process since the introspect is already solved.
