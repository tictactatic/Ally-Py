'''
Created on May 24, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths based on id property inputs.
'''

from ally.api.operator.type import TypeProperty, TypeModel
from ally.api.type import Input
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context, pushIn, cloneCollection
from ally.design.processor.handler import HandlerProcessor
import itertools
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    relations = defines(dict, doc='''
    @rtype: dictionary{TypeModel: set(TypeModel)}
    The model relations, as a key the model that depends on the models found in the value set.
    ''')
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class InvokerOnInput(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    solved = defines(set, doc='''
    @rtype: set(string)
    The input names of the caller that are solved on the invoker.
    ''')
    path = defines(list, doc='''
    @rtype: list[Context]
    The path elements.
    ''')
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    target = requires(TypeModel)
    location = requires(str)
    
class ElementInput(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The element name.
    ''')
    model = defines(TypeModel, doc='''
    @rtype: TypeModel
    The model represented by the element.
    ''')
    property = defines(TypeProperty, doc='''
    @rtype: TypeProperty
    The property represented by the element.
    ''')
    
# --------------------------------------------------------------------

class PathInputHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the paths based on id property inputs.
    '''
    
    def process(self, chain, register:Register, Invoker:InvokerOnInput, Element:ElementInput, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the paths based on property id inputs.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Invoker, InvokerOnInput), 'Invalid invoker %s' % Invoker
        assert issubclass(Element, ElementInput), 'Invalid element %s' % Element
        if not register.invokers: return  # No invoker to process
        
        assert isinstance(register.invokers, list), 'Invalid invokers %s' % register.invokers

        if register.relations is None: register.relations = {}
        ninvokers, k = [], 0
        while k < len(register.invokers):
            invoker = register.invokers[k]
            k += 1
            assert isinstance(invoker, InvokerOnInput), 'Invalid invoker %s' % invoker
            
            if invoker.solved is None: invoker.solved = set()
            mandatory, optional, properties = [], [], set()
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                
                if isinstance(inp.type, TypeProperty) and isinstance(inp.type.parent, TypeModel):
                    if inp.type in properties:
                        log.error('Cannot use because the %s should appear at most once, try using an alias '
                                  'on one of the annotations, at:%s', inp.type, invoker.location)
                        k -= 1
                        del register.invokers[k]
                        break
                    properties.add(inp.type)
                    invoker.solved.add(inp.name)
                    if inp.hasDefault: optional.append(inp)
                    else: mandatory.append(inp)
            else:
                if invoker.target:
                    relations = register.relations.get(invoker.target)
                    if relations is None: relations = register.relations[invoker.target] = set()
                    relations.add(prop.parent for prop in properties)
                elementsFor = [(invoker, mandatory)]
                if optional:
                    combinations = (itertools.combinations(optional, i) for i in range(1, len(optional) + 1))
                    for extra in itertools.chain(*combinations):
                        ninvoker = pushIn(Invoker(), invoker, interceptor=cloneCollection)
                        elementsFor.append((ninvoker, itertools.chain(mandatory, extra)))
                        ninvokers.append(ninvoker)
                        
                for invoker, inputs in elementsFor:
                    if invoker.path is None: invoker.path = []
                    for inp in inputs:
                        assert isinstance(inp.type, TypeProperty)
                        invoker.path.append(Element(name=inp.type.parent.name, model=inp.type.parent))
                        invoker.path.append(Element(property=inp.type))
                        
        register.invokers.extend(ninvokers)
