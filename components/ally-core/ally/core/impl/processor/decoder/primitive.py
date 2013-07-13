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

# --------------------------------------------------------------------
    
class DefinitionPrimitive(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitation = defines(Context, doc='''
    @rtype: Context
    The solicitation that this definition is based on.
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
    definitions = defines(list, doc='''
    @rtype: list[Context}
    Definitions containing representative data for create.
    ''')
    # ---------------------------------------------------------------- Required
    solicitations = requires(list)
                   
class Solicitation(Context):
    '''
    The decoder solicitation context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(str)
    devise = requires(IDevise)
    objType = requires(Type)
    
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
    converter = requires(Converter)
    
# --------------------------------------------------------------------

@injected
class PrimitiveDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive values decoding.
    '''
    
    def __init__(self):
        super().__init__(Solicitation=Solicitation, Support=Support)
        
    def process(self, chain, Definition:DefinitionPrimitive, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the primitive decode.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Definition, DefinitionPrimitive), 'Invalid definition class %s' % Definition
        
        if not create.solicitations: return 
        # There is not solicitation to process.
        
        k = 0
        while k < len(create.solicitations):
            sol = create.solicitations[k]
            k += 1
            
            assert isinstance(sol, Solicitation), 'Invalid solicitation %s' % sol
            decoder = self.createDecoder(sol.objType, sol.path, sol.devise)
            if decoder is None: continue
            # No primitive decoder available, just move along.
            
            k -= 1
            del create.solicitations[k]
            
            if create.decoders is None: create.decoders = []
            create.decoders.append(decoder)
            
            if create.definitions is None: create.definitions = []

            create.definitions.append(Definition(solicitation=sol, name=sol.path, type=sol.objType))
            
    def createDecoder(self, objType, path, devise):
        '''
        Called in order to create the decoder, provides None if no decoder can be created.
        '''
        assert isinstance(objType, Type), 'Invalid type %s' % objType
        if isinstance(objType, Iter): return
        # Cannot handle a collection, just move along.
        if not objType.isPrimitive: return
        # If the type is not primitive just move along.
        return DecoderPrimitive(path, devise, objType)

# --------------------------------------------------------------------

class DecoderPrimitive(IDecoder):
    '''
    Implementation for a @see: IDecoder for primitve types.
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
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        if path != self.path: return
        if not isinstance(obj, str): return
        # If the value is not a string then is not valid
        try: value = support.converter.asValue(obj, self.objType)
        except ValueError:
            if support.failures is None: support.failures = []
            support.failures.append('Invalid value \'%s\' for \'%s\'' % (obj, path))
        else: self.devise.set(target, value, support)
        return True
    
