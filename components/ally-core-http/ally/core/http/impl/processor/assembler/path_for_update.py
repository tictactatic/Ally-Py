'''
Created on May 30, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths adjustments for update invokers.
'''

from ally.api.operator.type import TypeModel, TypeProperty
from ally.core.impl.processor.assembler.base import excludeFrom, InvokerExcluded, \
    RegisterExcluding
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.exception import DevelError
from ally.http.spec.server import HTTP_PUT
from collections import Callable
from functools import partial
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(InvokerExcluded):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list)
    prepare = defines(Callable, doc='''
    @rtype: callable(dictionary{Type|string: object})
    A callable that prepares the arguments for invoking, takes in a dictionary of type or string to object mapping of 
    arguments.
    ''')
    # ---------------------------------------------------------------- Required
    methodHTTP = requires(str)
    target = requires(TypeModel)
    
class ElementUpdate(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str)
    property = defines(TypeProperty)
    # ---------------------------------------------------------------- Required
    model = requires(TypeModel)
    
# --------------------------------------------------------------------

class PathUpdateHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the invoker adjustments for updates.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:RegisterExcluding, Element:ElementUpdate, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the paths adjustments based on target models.
        '''
        assert isinstance(register, RegisterExcluding), 'Invalid register %s' % register
        assert issubclass(Element, ElementUpdate), 'Invalid element %s' % Element
        if not register.invokers: return

        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.methodHTTP != HTTP_PUT: continue
            if not invoker.target: continue
            assert isinstance(invoker.target, TypeModel), 'Invalid target %s' % invoker.target
            if not invoker.target.propertyId: continue
            
            if invoker.path is None: invoker.path = []
            for el in invoker.path:
                assert isinstance(el, ElementUpdate), 'Invalid element %s' % el
                if el.model == invoker.target:
                    log.error('Cannot use for update because the %s is already present as input, at:%s',
                              invoker.target, invoker.location)
                    excludeFrom(chain, invoker)
                    break
            else:
                invoker.path.append(Element(name=invoker.target.name, model=invoker.target))
                invoker.path.append(Element(property=invoker.target.propertyId))
                invoker.prepare = partial(self.prepare, invoker, invoker.prepare)
                
    # ----------------------------------------------------------------
    
    def prepare(self, invoker, wrapped, arguments):
        '''
        Prepares the arguments for invoking.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(invoker.target, TypeModel), 'Invalid target %s' % invoker.target
        assert isinstance(arguments, dict), 'Invalid arguments %s' % arguments
        assert isinstance(invoker.target.propertyId, TypeProperty)
        
        modelObj, idObj = arguments[invoker.target], arguments[invoker.target.propertyId]
        
        val = getattr(modelObj, invoker.target.propertyId.name)
        if val is None: setattr(modelObj, invoker.target.propertyId.name, idObj)
        elif val != idObj:
            raise DevelError('Cannot set value %s for \'%s\', expected value %s' % (val, invoker.target.propertyId.name, idObj))
       
        if wrapped: wrapped(arguments)
