'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the matcher data based on representation objects.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.transform.representation import Object, Collection
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import Handler, HandlerProcessorProceed
from assemblage.api.assemblage import Matcher
from collections import Iterable
import logging
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------
    
class DataAssemblage(Context):
    '''
    The data assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    matchers = defines(Iterable, doc='''
    @rtype: Iterable(DataMatcher)
    The matcher objects representations.
    ''')
    # ---------------------------------------------------------------- Required
    representation = requires(object)

class DataMatcherRepr(Context):
    '''
    The data matcher context.
    '''
    # ---------------------------------------------------------------- Defined
    models = defines(list, doc='''
    @rtype: list[Matcher]
    The matchers models of this mathcer.
    ''')
    representation = defines(object, doc='''
    @rtype: object
    The representation object for the target.
    ''')

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Optional
    matcherName = optional(str)
    # ---------------------------------------------------------------- Required
    required = requires(type)
    assemblages = requires(Iterable)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideMatchers')
class ProvideMatchers(HandlerProcessorProceed):
    '''
    Provides the matchers data.
    '''
    
    def __init__(self):
        super().__init__(DataAssemblage=DataAssemblage)
    
    def process(self, DataMatcher:DataMatcherRepr, obtain:Obtain, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the matchers data
        '''
        assert issubclass(DataMatcher, DataMatcherRepr), 'Invalid data class %s' % DataMatcher
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(obtain.assemblages, Iterable), 'Invalid assemblages %s' % obtain.assemblages
        
        if not obtain.required == Matcher: return  # Only the matcher needs representations 
        if Obtain.matcherName in obtain: name = obtain.matcherName
        else: name = None
        
        obtain.assemblages = self.processAssemblages(obtain.assemblages, DataMatcher, name)
        
    # ----------------------------------------------------------------
        
    def processAssemblages(self, datas, DataMatcher, name):
        '''
        Provides the matchers data.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        for data in datas:
            assert isinstance(data, DataAssemblage), 'Invalid data %s' % data
            
            if data.matchers is None: data.matchers = []
            
            obj = data.representation
            if name:
                assert isinstance(name, str), 'Invalid name %s' % name
                if isinstance(obj, Collection):
                    assert isinstance(obj, Collection)
                    if name == obj.item.name: obj = obj.item
                    else: obj = None
                elif isinstance(obj, Object):
                    assert isinstance(obj, Object)
                    for prop in obj.properties:
                        if isinstance(prop, Object) and prop.name == name:
                            obj = prop
                            break
                    else: obj = None
            
            if not obj or not self.processMatchers(obj, DataMatcher, data.matchers): continue
            yield data
    
    def processMatchers(self, obj, DataMatcher, matchers):
        '''
        Process the data matchers for the provided object.
        '''
        assert isinstance(matchers, list), 'Invalid matchers %s' % matchers
        if isinstance(obj, Collection):
            assert isinstance(obj, Collection)
            assert isinstance(obj.item, Object), 'Invalid object %s' % obj
            
            model = Matcher()
            model.Name = obj.item.name
            matchers.append(DataMatcher(models=[model], representation=obj.item))
            return True
        elif isinstance(obj, Object):
            assert isinstance(obj, Object)
            for obj in obj.properties:
                model = Matcher()
                model.Name = obj.name
                matchers.append(DataMatcher(models=[model], representation=obj))
            return True
        
        log.error('Cannot provide targets for representation %s', obj)
