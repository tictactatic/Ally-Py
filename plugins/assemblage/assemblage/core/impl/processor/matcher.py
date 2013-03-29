'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the matchers based on representation object.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.http.spec.transform.flags import ATTRIBUTE_REFERENCE
from ally.core.spec.transform.render import IPattern
from ally.core.spec.transform.representation import Object, Collection, \
    Attribute, Property
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from assemblage.api.assemblage import Matcher
from collections import Iterable
import itertools
import logging
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    result = defines(Iterable, doc='''
    @rtype: Iterable(Matcher)
    The generated matchers.
    ''')
    # ---------------------------------------------------------------- Required
    required = requires(object)
    representation = requires(object)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    pattern = requires(IPattern)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideMatchers')
class ProvideMatchers(HandlerProcessor):
    '''
    Provides the matchers.
    '''
    
    def process(self, chain, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the matchers.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        if obtain.required == Matcher:
            assert isinstance(support.pattern, IPattern), 'Invalid support pattern %s' % support.pattern
            
            matchers = self.processMatchers(obtain.representation, support.pattern)
            
            if obtain.result is None: obtain.result = matchers
            else: obtain.result = itertools.chain(obtain.result, matchers)
            return
        
        chain.proceed()
        
    # ----------------------------------------------------------------
        
    def processMatchers(self, obj, pattern):
        '''
        Process the structure matchers.
        
        @param obj: object
            The representation object to process the matchers for.
        @param pattern: IPattern
            The pattern support implementation.
        @return: Iterable(Matcher)
            The processed matchers.
        '''
        if isinstance(obj, Collection):
            assert isinstance(obj, Collection)
            assert isinstance(obj.item, Object), 'Invalid object %s' % obj
            
            for model in self.processMatchers(obj.item, pattern): yield model
            
        elif isinstance(obj, Object):
            assert isinstance(obj, Object)
            refer = self.attributeReference(obj)
            if refer:
                yield self.processPatterns(Matcher(), obj, pattern, refer)
                
            else:
                for objProp in obj.properties:
                    assert isinstance(objProp, (Object, Property)), 'Invalid object property %s' % objProp
                    
                    model = Matcher()
                    model.Name = objProp.name
                    yield self.processPatterns(model, objProp, pattern, self.attributeReference(objProp))
                
        else: log.error('Cannot provide targets for representation %s', obj)
        
    def processPatterns(self, model, obj, pattern, refer):
        '''
        Process the matcher patterns.
        
        @param model: Matcher
            The matcher model to process the patterns in.
        @param obj: object
            The representation object to process the pattern on.
        @param pattern: IPattern
            The pattern support implementation.
        @param refer: object
            The representation object that contains the reference.
        @return: Matcher
            The same matcher.
        '''
        assert isinstance(model, Matcher), 'Invalid matcher model %s' % model
        assert isinstance(obj, (Collection, Object, Property)), 'Invalid object %s' % obj
        assert isinstance(pattern, IPattern), 'Invalid pattern %s' % pattern
        # If no reference available then it makes no sense to capture the object
        
        model.Pattern = pattern.matcher(obj, refer is not None)
        if refer:
            if isinstance(obj, Object) and obj.properties:
                if model.Present is None: model.Present = []
                for objProp in obj.properties: model.Present.append(objProp.name)

            model.Reference = pattern.capture(refer)
        return model

    def attributeReference(self, obj):
        '''
        Provides the objects first reference attribute.
        
        @param obj: object
            The representation object to find the reference attribute in.
        @return: Attribute|None
            The reference attribute.
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
                if ATTRIBUTE_REFERENCE in attr.flags: return attr
        
