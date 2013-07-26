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
from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, CONSUMED, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util import firstOf
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    target = requires(TypeModel)

class Decoding(Context):
    '''
    The decoding context.
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
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doSet = requires(IDo)
    doGet = requires(IDo)

class Parameter(Context):
    '''
    The parameter context.
    '''
    # ---------------------------------------------------------------- Defined
    path = requires(list)
    
class DefinitionQuery(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    references = defines(list, doc='''
    @rtype: list[Context]
    The definition references that directly linked with this definition.
    ''')

# --------------------------------------------------------------------

@injected
class QueryDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the query values decoding.
    '''
    
    decodeQueryAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodeQueryAssembly, Assembly), \
        'Invalid order decode assembly %s' % self.decodeQueryAssembly
        super().__init__(Branch(self.decodeQueryAssembly).included())
        
    def process(self, chain, processing, decoding:Decoding, parameter:Parameter, invoker:Invoker,
                Definition:DefinitionQuery, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the query decodings.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(parameter, Parameter), 'Invalid parameter %s' % parameter
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert issubclass(Definition, DefinitionQuery), 'Invalid definition class %s' % Definition
    
        if not isinstance(decoding.type, TypeQuery): return
        # If the type is not query just move along.
        assert isinstance(decoding.type, TypeQuery)
        
        # If the query is for the target model then we will use simple names.
        if invoker.target == decoding.type.target: qpath = ()
        else: qpath = parameter.path
    
        keyargs.update(invoker=invoker, Definition=Definition)
        for cname, cprop in decoding.type.properties.items():
            assert isinstance(cprop, TypeProperty), 'Invalid property %s' % cprop
            assert isinstance(cprop.type, TypeCriteria), 'Invalid criteria %s' % cprop.type
            
            cpath = list(qpath)
            cpath.append(cname)
            
            definitions = {}
            for name, prop in cprop.type.properties.items():
                assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                cdecoding = decoding.__class__()
                assert isinstance(cdecoding, Decoding), 'Invalid decoding %s' % cdecoding
                
                cdecoding.parent = decoding
                cdecoding.doSet = self.createSet(decoding.doGet, decoding.doSet, cprop, prop)
                cdecoding.doGet = self.createGet(decoding.doGet, cprop, prop)
                cdecoding.property = prop
                cdecoding.type = prop.type
                
                cparameter = parameter.__class__()
                assert isinstance(cparameter, Parameter), 'Invalid parameter %s' % cparameter
                cparameter.path = list(cpath)
                cparameter.path.append(name)
                
                consumed, arg = processing.execute(CONSUMED, decoding=cdecoding, parameter=cparameter, **keyargs)
                if not consumed: continue
                assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
                if not arg.decoding.doDecode:
                    log.error('Cannot decode criteria property %s for query of %s', prop, decoding.type)
                    raise Abort(decoding)
                if arg.decoding.parameterDefinition: definitions[name] = arg.decoding.parameterDefinition
            
            if cprop.type.main:
                mdecoding = decoding.__class__()
                assert isinstance(mdecoding, Decoding), 'Invalid decoding %s' % mdecoding
                
                prop = firstOf(cprop.type.main.values())
                references = [defin for defin in map(definitions.get, cprop.type.main) if defin]
                
                mdecoding.parent = decoding
                mdecoding.doSet = self.createSet(decoding.doGet, decoding.doSet, cprop, *cprop.type.main.values())
                mdecoding.doGet = self.createGet(decoding.doGet, cprop, prop)
                mdecoding.property = cprop
                mdecoding.type = prop.type

                mparameter = parameter.__class__()
                assert isinstance(mparameter, Parameter), 'Invalid parameter %s' % mparameter
                mparameter.path = cpath
                
                consumed, arg = processing.execute(CONSUMED, decoding=mdecoding, definition=Definition(references=references),
                                                   parameter=mparameter, **keyargs)
                if not consumed: continue
                assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
                if not arg.decoding.doDecode:
                    log.error('Cannot decode main criteria properties %s for query of %s',
                              ', '.join(map(str, cprop.type.main.values())), decoding.type)
                    raise Abort(decoding)
                    
    # ----------------------------------------------------------------
    
    def createGet(self, getter, criteria, prop):
        '''
        Create the do get for criteria.
        '''
        assert isinstance(getter, IDo), 'Invalid getter %s' % getter
        assert isinstance(criteria, TypeProperty), 'Invalid criteria property %s' % criteria
        assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
        def doGet(target):
            '''
            Do get the criteria property value.
            '''
            assert isinstance(criteria, TypeProperty)
            assert isinstance(prop, TypeProperty)
            query = getter(target)
            if query is None: return
            if criteria not in query: return
            return getattr(getattr(query, criteria.name), prop.name)
        return doGet
    
    def createSet(self, getter, setter, criteria, *properties):
        '''
        Create the do set for criteria.
        '''
        assert isinstance(getter, IDo), 'Invalid getter %s' % getter
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        assert isinstance(criteria, TypeProperty), 'Invalid criteria property %s' % criteria
        assert properties, 'At least one property is required'
        if __debug__:
            for prop in properties: assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
        def doSet(target, value):
            '''
            Do set the criteria properties value.
            '''
            assert isinstance(criteria, TypeProperty)
            assert isinstance(criteria.parent, TypeQuery), 'Invalid criteria %s' % criteria
            query = getter(target)
            if query is None:
                query = criteria.parent.clazz()
                setter(target, query)
            target = getattr(query, criteria.name)
            for prop in properties:
                assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                setattr(target, prop.name, value)
        return doSet
