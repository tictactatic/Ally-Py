'''
Created on May 30, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths adjustments for update invokers.
'''

from ally.api.operator.type import TypeModel, TypeProperty
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_PUT
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
    # ---------------------------------------------------------------- Defined
    path = defines(list)
    # ---------------------------------------------------------------- Required
    methodHTTP = requires(str)
    target = requires(TypeModel)
    location = requires(str)
    
class ElementUpdate(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str)
    property = defines(TypeProperty)
    isInjected = defines(bool, doc='''
    @rtype: boolean
    If True indicates that the path element is actually to be injected inside a model entity.
    ''')
    # ---------------------------------------------------------------- Required
    model = requires(TypeModel)
    
# --------------------------------------------------------------------

class PathUpdateHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the invoker adjustments for updates.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:Register, Element:ElementUpdate, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the paths adjustments based on target models.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Element, ElementUpdate), 'Invalid element %s' % Element
        if not register.invokers: return

        aborted = []
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
                    aborted.append(invoker)
                    break
            else:
                invoker.path.append(Element(name=invoker.target.name, model=invoker.target))
                invoker.path.append(Element(property=invoker.target.propertyId, isInjected=True))

        if aborted: raise Abort(*aborted)
        
