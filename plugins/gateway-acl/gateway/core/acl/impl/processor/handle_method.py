'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Process the method handling.
'''

from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.method import Method
from gateway.core.acl.spec import ACTION_GET
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    accessMethods = requires(set)

class ACLAccess(Context):
    '''
    The ACL access context.
    '''
    # ---------------------------------------------------------------- Required
    methods = requires(dict)
    
class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    value = defines(object, doc='''
    @rtype: object
    The value required.
    ''')
    method = defines(Context, doc='''
    @rtype: Context
    The method that is targeted by 'forMethod'.
    ''')
    # ---------------------------------------------------------------- Required
    action = requires(str)
    target = requires(object)
    access = requires(Context)
    forMethod = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='handleMethod')
class HandleMethod(HandlerProcessor):
    '''
    Implementation for a processor that provides the method handling.
    '''
    
    def __init__(self):
        super().__init__(ACLAccess=ACLAccess)

    def process(self, chain, register:Register, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the permission handling.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        
        if solicit.forMethod is not None:
            if not register.accessMethods or solicit.forMethod not in register.accessMethods: return chain.cancel()
            if solicit.access:
                assert isinstance(solicit.access, ACLAccess), 'Invalid ACL access %s' % solicit.access
                if not solicit.access.methods: return chain.cancel()
                assert isinstance(solicit.access.methods, dict), 'Invalid access methods %s' % solicit.access.methods
                solicit.method = solicit.access.methods.get(solicit.forMethod)
                if not solicit.method: return chain.cancel()
        
        if solicit.action != ACTION_GET: return
        if solicit.target not in (Method, Method.Name): return
        
        if solicit.forMethod:
            if solicit.target == Method: solicit.value = self.create(solicit.forMethod)
            else: solicit.value = solicit.forMethod
            
        elif solicit.access:
            if not solicit.access.methods: return chain.cancel()
            if solicit.target == Method: values = (self.create(name) for name in solicit.access.methods)
            else: values = solicit.access.methods.keys()
            if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
            else: solicit.value = values
            
        else:
            if solicit.target == Method: values = (self.create(name) for name in register.accessMethods)
            else: values = register.accessMethods
            if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
            else: solicit.value = values

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the method.
        '''
        value = Method()
        value.Name = name
        
        return value
