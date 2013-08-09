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
from ally.design.processor.attribute import requires, defines, attribute
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import attributesOf, hasAttribute
from ally.support.util_spec import IDo
import itertools

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
    doCopyElement = attribute(IDo, doc='''
    @rtype: callable(destination:Context, source:Context, exclude:set=None) -> Context
    On the first position the destination element to copy to and on the second position the source to copy from, returns
    the destination element. Accepts also a named argument containing a set of attributes names to exclude.
    ''')
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    exclude = requires(set)
    doCopyInvoker = requires(IDo)
    
class InvokerOnInput(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list, doc='''
    @rtype: list[Context]
    The path elements.
    ''')
    # ---------------------------------------------------------------- Required
    id = requires(str)
    inputs = requires(tuple)
    target = requires(TypeModel)
    
class ElementInput(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The element name.
    ''')
    input = defines(Input, doc='''
    @rtype: Input
    The input represented by the element.
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
        assert issubclass(Invoker, InvokerOnInput), 'Invalid invoker class %s' % Invoker
        assert issubclass(Element, ElementInput), 'Invalid element %s' % Element
        
        if not register.invokers: return  # No invoker to process
        assert isinstance(register.invokers, list), 'Invalid invokers %s' % register.invokers
        
        register.doCopyElement = self.doCopyElement
        register.doCopyInvoker = self.createCopyInvoker(register.doCopyInvoker, register)

        if register.relations is None: register.relations = {}
        ninvokers = []
        for invoker in register.invokers:
            assert isinstance(invoker, InvokerOnInput), 'Invalid invoker %s' % invoker
            
            mandatory, optional = [], []
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                if isinstance(inp.type, TypeProperty) and isinstance(inp.type.parent, TypeModel):
                    if inp.hasDefault: optional.append(inp)
                    else: mandatory.append(inp)
                    
                    if invoker.target:
                        relations = register.relations.get(invoker.target)
                        if relations is None: relations = register.relations[invoker.target] = set()
                        relations.add(inp.type.parent)
                    
            elementsFor = [(invoker, mandatory)]
            if optional:
                combinations = (itertools.combinations(optional, i) for i in range(1, len(optional) + 1))
                for extra in itertools.chain(*combinations):
                    invokerId = '(%s mandatory for %s)' % (invoker.id, ','.join(inp.name for inp in extra))
                    if invokerId in register.exclude: continue
            
                    ninvoker = register.doCopyInvoker(Invoker(), invoker)
                    ninvoker.id = invokerId
                    elementsFor.append((ninvoker, itertools.chain(mandatory, extra)))
                    ninvokers.append(ninvoker)
                    
            for invoker, inputs in elementsFor:
                if invoker.path is None: invoker.path = []
                for inp in inputs:
                    assert isinstance(inp.type, TypeProperty)
                    invoker.path.append(Element(name=inp.type.parent.name, model=inp.type.parent))
                    invoker.path.append(Element(input=inp, property=inp.type))
                 
        register.invokers.extend(ninvokers)
        
    # ----------------------------------------------------------------
    
    def createCopyInvoker(self, doCopy, register):
        '''
        Create the invoker do copy.
        '''
        assert isinstance(doCopy, IDo), 'Invalid do copy %s' % doCopy
        assert isinstance(register, Register), 'Invalid register %s' % register
        def doCopyInvoker(destination, source, exclude=None):
            '''
            Do copy the invoker.
            '''
            assert isinstance(destination, InvokerOnInput), 'Invalid destination %s' % destination
            assert isinstance(source, InvokerOnInput), 'Invalid source %s' % source
            assert exclude is None or isinstance(exclude, set), 'Invalid exclude %s' % exclude
            
            if not exclude or 'path' not in exclude:
                if destination.path is None and source.path is not None:
                    assert isinstance(register.doCopyElement, IDo), 'Invalid do copy %s' % register.doCopyElement
                    destination.path = [register.doCopyElement(el.__class__(), el) for el in source.path]
            return doCopy(destination, source, exclude)
        
        return doCopyInvoker

    def doCopyElement(self, destination, source, exclude=None):
        '''
        Do copy the element.
        '''
        assert isinstance(destination, ElementInput), 'Invalid destination %s' % destination
        assert isinstance(source, ElementInput), 'Invalid source %s' % source
        assert exclude is None or isinstance(exclude, set), 'Invalid exclude %s' % exclude
        
        for name in attributesOf(destination):
            if exclude and name in exclude: continue
            value = getattr(destination, name)
            if value is not None: continue
            if not hasAttribute(source, name): continue
            value = getattr(source, name)
            if value is None: continue
            if isinstance(value, (set, list, dict, Context)):
                raise Exception('Cannot copy \'%s\' with value \'%s\'' % (name, value))
            setattr(destination, name, value)
        
        return destination
