'''
Created on May 29, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the domain for the path.
'''

from ally.api.operator.type import TypeModel
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    hintsModel = definesIf(dict)
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    exclude = requires(set)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list)
    # ---------------------------------------------------------------- Required
    id = requires(str)
    location = requires(str)
    
class ElementDomain(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str)
    # ---------------------------------------------------------------- Required
    model = requires(TypeModel)
    
# --------------------------------------------------------------------

@injected
class PathDomainHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the domain based on path elements models.
    '''
    
    hintName = 'domain'
    # The hint name for the model domain.
    hintDescription = '(string) The domain where the model is registered'
    # The hint description.
    
    def __init__(self):
        assert isinstance(self.hintName, str), 'Invalid hint name %s' % self.hintName
        assert isinstance(self.hintDescription, str), 'Invalid hint description %s' % self.hintDescription
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:Register, Element:ElementDomain, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the domain based on elements models.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Element, ElementDomain), 'Invalid path element %s' % Element
        assert isinstance(register.exclude, set), 'Invalid exclude set %s' % register.exclude
        
        if Register.hintsModel in register:
            if register.hintsModel is None: register.hintsModel = {}
            register.hintsModel[self.hintName] = self.hintDescription
        
        if not register.invokers: return

        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.path: continue  # No path model to process for.
            assert isinstance(invoker.path, list), 'Invalid elements %s' % invoker.path
            
            for el in invoker.path:
                assert isinstance(el, ElementDomain), 'Invalid element %s' % el
                if not el.model: continue
                assert isinstance(el.model, TypeModel), 'Invalid model %s' % el.model
                
                if self.hintName in el.model.hints:
                    domain = el.model.hints[self.hintName]
                    if not isinstance(domain, str) or not domain:
                        log.error('Cannot use invoker because the model %s domain \'%s\' is invalid, at:%s',
                                  el.model, domain, invoker.location)
                        register.exclude.add(invoker.id)
                        chain.cancel()
                    else:
                        assert isinstance(domain, str)
                        for name in reversed(domain.split('/')):
                            if name: invoker.path.insert(0, Element(name=name))
                break
