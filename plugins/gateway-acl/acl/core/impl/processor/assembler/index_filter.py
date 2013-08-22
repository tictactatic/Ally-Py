'''
Created on Aug 12, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Indexes the filters invokers.
'''

from acl.api.filter import IFilterService, Filter
from acl.core.spec import uniqueNameFor
from ally.api.operator.type import TypeProperty
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
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
    filterName = requires(str)
    location = requires(str)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='indexFilter')
class IndexFilterHandler(HandlerProcessor):
    '''
    Implementation for a processor that indexes the filters invokers.
    '''
    
    filterService = IFilterService; wire.entity('filterService')
    
    def __init__(self):
        assert isinstance(self.filterService, IFilterService), 'Invalid filter service %s' % self.filterService
        super().__init__(Invoker=Invoker, Element=Element)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Merge the filter invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return
        
        aborted, filters = [], {}
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.filterName is None: continue
            
            target, items = None, []
            for el in invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if el.property:
                    if target is None:
                        target = el.property
                        items.append('*')
                    else:
                        log.error('Cannot use filter invoker because there are to many targets available, at:%s',
                                  invoker.location)
                        aborted.append(invoker)
                        break
                else:
                    assert isinstance(el.name, str), 'Invalid element name %s' % el.name
                    items.append(el.name)
            else:
                if target is None:
                    log.error('Cannot use filter invoker because there is not target available, at:%s', invoker.location)
                    aborted.append(invoker)
                    continue
                
            if invoker.filterName not in filters:
                filtre, target, invokers = filters[invoker.filterName] = Filter(), target, [invoker]
                filtre.Paths = []
            else:
                filtre, ptarget, invokers = filters[invoker.filterName]
                if target != ptarget:
                    log.error('Cannot use filter invoker at:%s\n, because target is incompatible with filters at:%s',
                              invoker.location, ''.join(invk.location for invk in invokers))
                    aborted.append(invoker)
                    continue
                invokers.append(invoker)
                
            filtre.Paths.append('/'.join(items))
        
        if aborted: raise Abort(*aborted)
        
        for name, (filtre, target, invokers) in filters.items():
            filtre.Name = name
            filtre.Target = uniqueNameFor(target)
            filtre.Paths.sort()
            
            try: present = self.filterService.getById(name)
            except: assert log.debug('There is no filter for \'%s\'', name) or True
            else:
                if equalContainer(filtre, present): return
                log.info('Removing filter %s since is not compatible with the current structure', present)
                self.filterService.delete(name)
            
            self.filterService.insert(filtre)
            assert log.debug('Added filter %s', filtre) or True
