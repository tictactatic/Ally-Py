'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the access names and objects.
'''

from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api import access
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    access = requires(dict)

class Access(Context):
    '''
    The access context.
    '''
    # ---------------------------------------------------------------- Required
    pattern = requires(str)
    
class Get(Context):
    '''
    The get context.
    '''
    # ---------------------------------------------------------------- Defined
    value = defines(object, doc='''
    @rtype: object
    The value required.
    ''')
    # ---------------------------------------------------------------- Required
    target = requires(object)
    forName = requires(str)
    forAll = requires(bool)
    
# --------------------------------------------------------------------

@setup(Handler, name='getAccess')
class GetAccess(HandlerProcessor):
    '''
    Implementation for a processor that provides the access names and objects.
    '''
    
    def __init__(self):
        super().__init__(Access=Access)

    def process(self, chain, register:Register, get:Get=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the access.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.access: return
        assert isinstance(register.access, dict), 'Invalid access %s' % register.access
        if not get: return
        assert isinstance(get, Get), 'Invalid get access %s' % get
        if get.target not in (access.Access, access.Access.Name): return
        
        if get.forName is not None:
            acc = register.access.get(get.forName)
            if not acc: return chain.cancel()
            assert isinstance(acc, Access), 'Invalid access %s' % acc
            if get.target == access.Access: get.value = self.create(get.forName, acc)
            else: get.value = get.forName
            
        elif get.forAll:
            if get.target == access.Access: values = (self.create(name, acc) for name, acc in register.access.items())
            else: values = register.access.keys()
            if get.value is not None: get.value = itertools.chain(get.value, values)
            else: get.value = values

    # ----------------------------------------------------------------
    
    def create(self, name, acc):
        '''
        Create the access.
        '''
        assert isinstance(acc, Access), 'Invalid access %s' % acc
        
        value = access.Access()
        value.Name = name
        value.Pattern = acc.pattern
        
        return value
