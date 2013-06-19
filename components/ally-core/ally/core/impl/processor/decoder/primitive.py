'''
Created on Jun 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive types decoding.
'''

from ally.api.type import Type, Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Converter
from ally.core.spec.transform.encdec import IDecoder, IDevise
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import deque
import re

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    definitions = defines(dict)

class DefinitionPrimitive(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context, doc='''
    @rtype: Context
    The parent definition.
    ''')
    name = defines(str, doc='''
    @rtype: string
    The name of the definition.
    ''')
    type = defines(Type, doc='''
    @rtype: Type
    The type of the definition.
    ''')

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    decoders = defines(list, doc='''
    @rtype: list[IDecoder]
    The created decoders.
    ''')
    # ---------------------------------------------------------------- Required
    solicitaions = requires(list)
                   
class Solicitaion(Context):
    '''
    The decoder solicitaion context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(object)
    devise = requires(IDevise)
    objType = requires(Type)
    key = requires(frozenset)
    definition = requires(Context)
    
class Support(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    failures = defines(list, doc='''
    @rtype: list[string]
    The decoding failures that occurred.
    ''')
    # ---------------------------------------------------------------- Required
    converterPath = requires(Converter)
    
# --------------------------------------------------------------------

@injected
class PrimitiveDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive values decoding.
    '''
    
    regexSplit = re.compile('[\s]*(?<!\\\)\,[\s]*')
    # The regex used for splitting list values.
    regexNormalize = re.compile('\\\(?=\,)')
    # The regex used for normalizing the split values.
    
    def __init__(self):
        assert self.regexSplit, 'Invalid regex for values split %s' % self.regexSplit
        assert self.regexNormalize, 'Invalid regex for value normalize %s' % self.regexNormalize
        super().__init__(Solicitaion=Solicitaion, Support=Support)
        
    def process(self, chain, invoker:Invoker, Definition:DefinitionPrimitive, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the primitive decode.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Definition, DefinitionPrimitive), 'Invalid definition class %s' % Definition
        
        if not create.solicitaions: return 
        # There is not solicitaion to process.
        
        k = 0
        while k < len(create.solicitaions):
            sol = create.solicitaions[k]
            k += 1
            
            assert isinstance(sol, Solicitaion), 'Invalid solicitation %s' % sol
            assert isinstance(sol.objType, Type), 'Invalid type %s' % sol.objType
            if not sol.objType.isPrimitive: continue
            # If the type is not primitive just move along.
            
            k -= 1
            del create.solicitaions[k]
            
            if isinstance(sol.objType, Iter):
                assert isinstance(sol.objType, Iter)
                decoder = DecoderSimpleList(sol.path, sol.devise, sol.objType.itemType, self.regexSplit, self.regexNormalize)
            else:
                decoder = DecoderSimple(sol.path, sol.devise, sol.objType)
            
            if create.decoders is None: create.decoders = []
            create.decoders.append(decoder)
        
            if invoker.definitions is None: invoker.definitions = {}
            definition = invoker.definitions.get(sol.key)
            if not definition: definition = invoker.definitions[sol.key] = Definition()
            assert isinstance(definition, DefinitionPrimitive), 'Invalid definition %s' % definition
            definition.parent, definition.name, definition.type = sol.definition, sol.path, sol.objType

# --------------------------------------------------------------------

class DecoderSimple(IDecoder):
    '''
    Implementation for a @see: IDecoder for simple types.
    '''
    
    def __init__(self, path, devise, objType):
        '''
        Construct the simple type decoder.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(objType, Type), 'Invalid object type %s' % objType
        
        self.path = path
        self.devise = devise
        self.objType = objType
        
    def decode(self, path, obj, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.converterPath, Converter), 'Invalid converter %s' % support.converterPath
        
        if path != self.path: return
        if not isinstance(obj, str): return
        # If the value is not a string then is not valid
        try: value = support.converterPath.asValue(obj, self.objType)
        except ValueError:
            if support.failures is None: support.failures = []
            support.failures.append('Invalid value \'%s\' for \'%s\'' % (obj, path))
        else: self.devise.set(target, value, support)
        return True
    
class DecoderSimpleList(IDecoder):
    '''
    Implementation for a @see: IDecoder for simple list types.
    '''
    
    def __init__(self, path, devise, itemType, split, normalize):
        '''
        Construct the simple list type decoder.
        '''
        assert split, 'Invalid regex for values split %s' % split
        assert normalize, 'Invalid regex for value normalize %s' % normalize
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(itemType, Type), 'Invalid item type %s' % itemType
        
        self.path = path
        self.devise = devise
        self.itemType = itemType
        self.split = split
        self.normalize = normalize
        
    def decode(self, path, obj, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.converterPath, Converter), 'Invalid converter %s' % support.converterPath
        
        if path != self.path: return
        if isinstance(obj, str):
            obj = self.split.split(obj)
            for k in range(0, len(obj)): obj[k] = self.normalize.sub('', obj[k])
        if not isinstance(obj, (list, tuple, deque)): obj = (obj,)

        values = []
        for item in obj:
            if not isinstance(item, str): continue
            try: values.append(support.converterPath.asValue(item, self.itemType))
            except ValueError:
                if support.failures is None: support.failures = []
                support.failures.append('Invalid item \'%s\' for \'%s\'' % (item, path))
            
        previous = self.devise.get(target)
        if previous is None: self.devise.set(target, values, support)
        else:
            assert isinstance(previous, list), 'Invalid previous value %s' % previous
            previous.extend(values)
        return True
