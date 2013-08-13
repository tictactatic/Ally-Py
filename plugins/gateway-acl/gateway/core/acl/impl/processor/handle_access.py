'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Process the access handling.
'''

from ..base import ACTION_GET
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.access import Access
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    accesses = requires(dict)

class ACLAccess(Context):
    '''
    The ACL access context.
    '''
    # ---------------------------------------------------------------- Required
    pattern = requires(str)

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    value = defines(object, doc='''
    @rtype: object
    The value required.
    ''')
    access = definesIf(Context, doc='''
    @rtype: Context
    The access that is targeted by 'forAccess'.
    ''')
    # ---------------------------------------------------------------- Required
    action = requires(str)
    target = requires(object)
    forAccess = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='handleAccess')
class HandleAccess(HandlerProcessor):
    '''
    Implementation for a processor that provides the access handling.
    '''
    
    def __init__(self):
        super().__init__(ACLAccess=ACLAccess)

    def process(self, chain, register:Register, solicit:Solicit, ** keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the access handling.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        if not register.accesses: return chain.cancel()
        
        assert isinstance(register.accesses, dict), 'Invalid ACL accesses %s' % register.accesses
        if solicit.forAccess is not None:
            access = register.accesses.get(solicit.forAccess)
            if not access: return chain.cancel()
            if Solicit.access in solicit: solicit.access = access
        else: access = None
        
        if solicit.action != ACTION_GET: return
        if solicit.target not in (Access, Access.Name): return
        
        if access:
            assert isinstance(access, ACLAccess), 'Invalid ACL access %s' % access
            if solicit.target == Access: solicit.value = self.create(solicit.forAccess, access)
            else: solicit.value = solicit.forAccess
        
        else:
            if solicit.target == Access: values = (self.create(name, acc) for name, acc in register.access.items())
            else: values = register.accesses.keys()
            if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
            else: solicit.value = values
            
    # ----------------------------------------------------------------
    
    def create(self, name, acc):
        '''
        Create the access.
        '''
        assert isinstance(acc, ACLAccess), 'Invalid access %s' % acc
        
        value = Access()
        value.Name = name
        value.Pattern = acc.pattern
        
        return value
