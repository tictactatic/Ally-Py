'''
Created on Mar 27, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the identifiers method override exclude headers.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from ally.http.spec.server import HTTP_GET, HTTP_POST, HTTP_DELETE, HTTP_PUT
from assemblage.api.assemblage import Identifier
from collections import Iterable

# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Optional
    result = optional(Iterable)
    # ---------------------------------------------------------------- Required
    required = requires(object)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='registerMethodOverride')
class RegisterMethodOverride(HandlerProcessor):
    '''
    Provides the identifiers method override, basically support for @see: MethodOverrideHandler.
    '''
    pattern_xmethod_override = 'X\-HTTP\-Method\-Override\\:\s*%s\s*$(?i)'; wire.config('pattern_xmethod_override', doc='''
    The header pattern for the method override, needs to contain '%s' where the value will be placed.
    ''')
    methods_override = {
                        HTTP_GET: [HTTP_DELETE],
                        HTTP_POST: [HTTP_PUT],
                        }; wire.config('methods_override', doc='''
    A dictionary containing as a key the overriden method and as a value the methods that are overrided.
    ''')
    
    def __init__(self):
        '''
        Construct the populate method override filter.
        '''
        assert isinstance(self.pattern_xmethod_override, str), \
        'Invalid method override pattern %s' % self.pattern_xmethod_override
        assert isinstance(self.methods_override, dict), 'Invalid methods override %s' % self.methods_override
        super().__init__()
        
    def process(self, chain, obtain:Obtain, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the method override to identifiers.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        
        chain.proceed()
        
        if obtain.required == Identifier:
            def callBack():
                assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
                if obtain.result is not None: obtain.result = self.register(obtain.result)
            chain.callBack(callBack)
            
    # ----------------------------------------------------------------
            
    def register(self, identifiers):
        '''
        Register the method override identifiers based on the provided identifiers.
        '''
        assert isinstance(identifiers, Iterable), 'Invalid identifiers %s' % identifiers
        for identifier in identifiers:
            assert isinstance(identifier, Identifier), 'Invalid identifier %s' % identifier
            
            override = self.methods_override.get(identifier.Method)
            if override:
                if Identifier.HeadersExclude not in identifier: identifier.HeadersExclude = []
                for method in override:
                    identifier.HeadersExclude.append(self.pattern_xmethod_override % method)
            
            yield identifier
