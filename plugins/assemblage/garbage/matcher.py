'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the matchers based on representation objects.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.http.spec.transform.flags import ATTRIBUTE_REFERENCE
from ally.core.spec.transform.render import IPattern
from ally.core.spec.transform.representation import Object, Collection, \
    Attribute, Property
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
    # ---------------------------------------------------------------- Required
    representation = requires(object)

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    objects = defines(Iterable, doc='''
    @rtype: Iterable(Assemblage)
    The generated matchers.
    ''')
    # ---------------------------------------------------------------- Optional
    matcherName = optional(str)
    # ---------------------------------------------------------------- Required
    required = requires(type)
    assemblages = requires(Iterable)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    pattern = requires(IPattern)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideMatchers')
class ProvideMatchers(HandlerProcessorProceed):
    '''
    Provides the matchers.
    '''
    
    def __init__(self):
        super().__init__(DataAssemblage=DataAssemblage)
    
    def process(self, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the matchers.
        '''
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(obtain.assemblages, Iterable), 'Invalid assemblages %s' % obtain.assemblages
        
        if not obtain.required == Matcher: return  # Only the matcher needs representations 
        assert isinstance(support.pattern, IPattern), 'Invalid support pattern %s' % support.pattern
        
        if Obtain.matcherName in obtain: name = obtain.matcherName
        else: name = None
        
        obtain.objects = self.processMatchers(obtain.assemblages, name, support.pattern)
        
    # ----------------------------------------------------------------
        
    def processMatchers(self, datas, name, pattern):
        '''
        Process the assemblages matchers.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        for data in datas:
            assert isinstance(data, DataAssemblage), 'Invalid data %s' % data
            
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
            
            if not obj: continue
            
            for model in self.processMatchersForObject(obj, pattern): yield model
    
    def processMatchersForObject(self, obj, pattern):
        '''
        Process the matchers for the provided object.
        '''
        if isinstance(obj, Collection):
            assert isinstance(obj, Collection)
            assert isinstance(obj.item, Object), 'Invalid object %s' % obj
            
            model = Matcher()
            model.Name = obj.item.name
            self.processPatterns(model, obj.item, pattern)
            yield model
            
        elif isinstance(obj, Object):
            assert isinstance(obj, Object)
            for objProp in obj.properties:
                assert isinstance(objProp, (Object, Property)), 'Invalid object property %s' % objProp
                
                model = Matcher()
                model.Name = objProp.name
                self.processPatterns(model, objProp, pattern)
                yield model
            
        else:
            log.error('Cannot provide targets for representation %s', obj)
        
    def processPatterns(self, model, obj, pattern):
        '''
        Process the matcher for the provided representation object.
        '''
        assert isinstance(model, Matcher), 'Invalid matcher model %s' % model
        assert isinstance(obj, (Collection, Object, Property)), 'Invalid object %s' % obj
        assert isinstance(pattern, IPattern), 'Invalid pattern %s' % pattern
        
        injected = self.hasReference(obj)
        if isinstance(obj, Object) and not injected: return
        # If no reference available then it makes no sense to capture the object
        
        model.Pattern = pattern.matcher(obj, injected)

    def hasReference(self, obj):
        '''
        Checks if the provided object has reference attributes.
        '''
        if isinstance(obj, Object):
            assert isinstance(obj, Object)
            attributes = obj.attributes
        elif isinstance(obj, Collection):
            assert isinstance(obj, Collection)
            attributes = obj.attributes
        else: attributes = None
        
        if attributes:
            for attr in obj.attributes.values():
                assert isinstance(attr, Attribute)
                if ATTRIBUTE_REFERENCE in attr.flags: return True
        
        return False
