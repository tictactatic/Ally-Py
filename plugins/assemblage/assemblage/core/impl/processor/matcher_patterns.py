'''
Created on Mar 25, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the matcher patterns.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.transform.render import IPattern
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import Handler, HandlerProcessorProceed
from ally.support.api.util_service import copy
from ally.support.util import lastCheck
from assemblage.api.assemblage import Matcher
from collections import Iterable
import logging
from ally.core.spec.transform.representation import Object, Attribute, \
    Collection
from ally.core.http.spec.transform.flags import ATTRIBUTE_REFERENCE
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------
    
class DataAssemblage(Context):
    '''
    The data assemblage context.
    '''
    # ---------------------------------------------------------------- Required
    matchers = requires(Iterable)
    
class DataMatcher(Context):
    '''
    The data matcher context.
    '''
    # ---------------------------------------------------------------- Required
    models = requires(list)
    representation = requires(object)

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Required
    required = requires(type)
    assemblages = requires(Iterable)
    
class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    patterns = requires(list)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideMatcherPatterns')
class ProvideMatcherPatterns(HandlerProcessorProceed):
    '''
    Provides the matchers patterns.
    '''
    
    def __init__(self):
        super().__init__(DataAssemblage=DataAssemblage, DataMatcher=DataMatcher)
    
    def process(self, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the matcher patterns
        '''
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(obtain.assemblages, Iterable), 'Invalid assemblages %s' % obtain.assemblages
        
        if not obtain.required == Matcher: return  # Only the matcher need patterns 
        
        obtain.assemblages = self.processAssemblages(obtain.assemblages, support)
        
    # ----------------------------------------------------------------
        
    def processAssemblages(self, datas, support):
        '''
        Provides the matchers data.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.patterns, list), 'Invalid support patterns %s' % support.patterns
        for data in datas:
            assert isinstance(data, DataAssemblage), 'Invalid data %s' % data
            assert isinstance(data.matchers, Iterable), 'Invalid data matchers %s' % data.matchers
            
            for datam in data.matchers:
                assert isinstance(datam, DataMatcher), 'Invalid matcher data %s' % datam
                assert isinstance(datam.models, list), 'Invalid data models %s' % datam.models
                assert datam.models, 'At least one model is required'
                
                injected = self.hasReference(datam.representation)
                if isinstance(datam.representation, Object) and not injected: continue
                # If no reference available then it makes no sense to capture the object
                
                model = datam.models[0]
                assert isinstance(model, Matcher), 'Invalid matcher model %s' % model
                for isLast, (pattern, types) in lastCheck(support.patterns):
                    assert isinstance(pattern, IPattern), 'Invalid pattern %s' % pattern
                    assert isinstance(types, Iterable), 'Invalid types %s' % types
                    
                    model.Types = list(types)
                    model.Pattern = pattern.matcher(datam.representation, injected)
                    
                    if not isLast:
                        # We make a clone for the next patterns
                        model = copy(model, Matcher())
                        datam.models.append(model)
            
            yield data
            
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
