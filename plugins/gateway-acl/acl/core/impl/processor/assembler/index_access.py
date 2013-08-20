'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Indexes the access invokers.
'''

from acl.api.access import IAccessService, Access
from acl.core.spec import uniqueNameFor, generateId
from ally.api.operator.type import TypeProperty
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.support.api.util_service import equalContainer
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)
    methodHTTP = requires(str)
    filterName = requires(str)
    shadowOf = requires(Context)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='indexAccess')
class IndexAccessHandler(HandlerProcessor):
    '''
    Implementation for a processor that indexes the access invokers by name.
    '''
    
    accessService = IAccessService; wire.entity('accessService')
    
    def __init__(self):
        assert isinstance(self.accessService, IAccessService), 'Invalid access service %s' % self.accessService
        super().__init__(Invoker=Invoker, Element=Element)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Merge the access invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No root to process
        
        shadows = []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.filterName is not None: continue
            if invoker.shadowOf:
                shadows.append(invoker)
                continue
            
            self.mergeAccess(invoker)
            
        for invoker in shadows: self.mergeAccess(invoker)

    # ----------------------------------------------------------------
    
    def mergeAccess(self, invoker):
        '''
        Creates and persist the access for the provided invoker.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        access = Access()
        access.Method = invoker.methodHTTP
        access.Types, items = [], []
        for el in invoker.path:
            assert isinstance(el, Element), 'Invalid element %s' % el
            if el.property:
                access.Types.append(uniqueNameFor(el.property))
                items.append('*')
            else:
                assert isinstance(el.name, str), 'Invalid element name %s' % el.name
                items.append(el.name)
        access.Path = '/'.join(items)
            
        if invoker.shadowOf:
            assert isinstance(invoker.shadowOf, Invoker), 'Invalid invoker %s' % invoker.shadowOf
            access.ShadowOf = generateId('/'.join('*' if el.property else el.name for el in invoker.shadowOf.path),
                                         invoker.shadowOf.methodHTTP)
        
        try: present = self.accessService.getById(generateId(access.Path, access.Method))
        except: assert log.debug('There is no access for \'%s\' with %s', access.Path, access.Method) or True
        else:
            assert present.Path == access.Path, \
            'Problems with hashing, hash %s it is the same for \'%s\' and \'%s\'' % (access.Id, present.Path, access.Path)
            if equalContainer(access, present, exclude=('Id',)): return
            log.info('Removing access %s since is not compatible with the current structure', present)
            self.accessService.delete(present.Id)
        
        self.accessService.insert(access)
        assert log.debug('Added access %s', access) or True
