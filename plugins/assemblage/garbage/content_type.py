'''
Created on Mar 26, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content types.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.transform.render import IPattern
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import Handler, HandlerProcessorProceed
from assemblage.api.assemblage import Type
from collections import Iterable
from itertools import chain

# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    objects = defines(Iterable, doc='''
    @rtype: Iterable(Type)
    The generated types.
    ''')
    # ---------------------------------------------------------------- Optional
    typeId = optional(str)
    # ---------------------------------------------------------------- Required
    required = requires(type)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    pattern = defines(IPattern, doc='''
    @rtype: IPattern
    The pattern to be used in generating the matchers.
    ''')
    # ---------------------------------------------------------------- Defined
    patterns = requires(list)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideTypes')
class ProvideTypes(HandlerProcessorProceed):
    '''
    Provides the types.
    '''
    
    def process(self, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the types.
        '''
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.patterns, list), 'Invalid support patterns %s' % support.patterns
        
        if Obtain.typeId in obtain: typeId = obtain.typeId
        else: typeId = None
        
        if typeId:
            for identifier, types, pattern in support.patterns:
                if identifier == typeId:
                    support.pattern = pattern
                    break
        
            if not obtain.required == Type: return  # No types need to be generated
        
            contentTypes = []
            for identifier, types, pattern in support.patterns:
                if identifier == typeId: 
                    contentType = Type()
                    contentType.Id = identifier
                    contentType.Types = types
                    contentTypes.append(contentType)
                    break
                
        if not obtain.required == Type: return  # No types need to be generated
        
        contentTypes = []
        for identifier, types, pattern in support.patterns:
            contentType = Type()
            contentType.Id = identifier
            contentType.Types = types
            contentTypes.append(contentType)
        
        if obtain.objects is None: obtain.objects = contentTypes
        else: obtain.objects = chain(obtain.objects, contentTypes)
        
