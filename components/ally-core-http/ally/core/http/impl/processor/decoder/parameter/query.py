'''
Created on Jun 18, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the queries types decoding.
'''

from ally.api.operator.type import TypeQuery, TypeProperty, TypeCriteria, \
    TypeModel
from ally.container.ioc import injected
from ally.core.impl.processor.decoder.base import RequestDecoding, DefineCreate
from ally.core.spec.transform.encdec import IDevise
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util import firstOf

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    target = requires(TypeModel)

class DecodingQuery(RequestDecoding):
    '''
    The query decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context, doc='''
    @rtype: Context
    The parent decoding that this decoding is based on.
    ''')
    property = defines(TypeProperty, doc='''
    @rtype: TypeProperty
    The property that represents the decoding.
    ''')
    references = defines(list, doc='''
    @rtype: list[Context]
    The decoding references that directly linked with this decoding.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(list)

# --------------------------------------------------------------------

@injected
class QueryDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the query values decoding.
    '''
    
    def __init__(self):
        super().__init__()
        
    def process(self, chain, create:DefineCreate, invoker:Invoker, Decoding:DecodingQuery, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the query decodings.
        '''
        assert isinstance(create, DefineCreate), 'Invalid create %s' % create
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert issubclass(Decoding, DecodingQuery), 'Invalid decoding class %s' % Decoding
        
        if not create.decodings: return 
        # There is not decodings to process.
        
        k, decodings = 0, []
        while k < len(create.decodings):
            decoding = create.decodings[k]
            k += 1
            
            assert isinstance(decoding, DecodingQuery), 'Invalid decoding %s' % decoding
            
            if not isinstance(decoding.type, TypeQuery): continue
            # If the type is not query just move along.
            assert isinstance(decoding.type, TypeQuery)
            
            k -= 1
            del create.decodings[k]
            
            qpath = list(decoding.path)
            # If the query is for the target model then we will use simple names.
            if invoker.target == decoding.type.target and qpath: qpath.pop()
        
            for cname, cprop in decoding.type.properties.items():
                assert isinstance(cprop, TypeProperty), 'Invalid property %s' % cprop
                assert isinstance(cprop.type, TypeCriteria), 'Invalid criteria %s' % cprop.type
                
                cpath = list(qpath)
                cpath.append(cname)
                
                decodingByProp = {}
                for name, prop in cprop.type.properties.items():
                    assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                    cdecoding = Decoding()
                    decodings.append(cdecoding)
                    decodingByProp[prop] = cdecoding
                    assert isinstance(cdecoding, DecodingQuery), 'Invalid decoding %s' % cdecoding
                    
                    cdecoding.parent = decoding
                    cdecoding.path = list(cpath)
                    cdecoding.path.append(name)
                    cdecoding.devise = DeviseCriteria(decoding.devise, cprop, prop)
                    cdecoding.property = prop
                    cdecoding.type = prop.type
                
                if cprop.type.main:
                    mdecoding = Decoding()
                    decodings.append(mdecoding)
                    assert isinstance(mdecoding, DecodingQuery), 'Invalid decoding %s' % mdecoding
                    
                    mdecoding.parent = decoding
                    mdecoding.path = cpath
                    mdecoding.devise = DeviseCriteria(decoding.devise, cprop, *cprop.type.main.values())
                    mdecoding.property = cprop
                    mdecoding.type = firstOf(cprop.type.main.values()).type
                    mdecoding.references = [decodingByProp[prop] for prop in cprop.type.main.values()]
                    
        create.decodings.extend(decodings)

# --------------------------------------------------------------------

class DeviseCriteria(IDevise):
    '''
    Implementation for @see: IDevise for handling criteria properties.
    '''
    
    def __init__(self, devise, criteria, *properties):
        '''
        Construct the devise criteria.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(criteria, TypeProperty), 'Invalid criteria property %s' % criteria
        assert properties, 'At least one property is required'
        if __debug__:
            for prop in properties: assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
        
        self.devise = devise
        self.criteria = criteria
        self.properties = properties
        
    def get(self, target):
        '''
        @see: IDevise.get
        '''
        query = self.devise.get(target)
        if query is None: return
        if self.criteria not in query: return
        return getattr(getattr(query, self.criteria.name), self.properties[0].name)
        
    def set(self, target, value):
        '''
        @see: IDevise.set
        '''
        query = self.devise.get(target)
        if query is None:
            query = self.criteria.parent.clazz()
            self.devise.set(target, query)
        target = getattr(query, self.criteria.name)
        for prop in self.properties:
            assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
            setattr(target, prop.name, value)
