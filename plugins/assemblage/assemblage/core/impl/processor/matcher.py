'''
Created on Mar 25, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the matchers for resource data.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from assemblage.api.assemblage import Matcher
from collections import Iterable
import itertools
                   
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

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Required
    assemblages = requires(Iterable)
    required = requires(type)
    # ---------------------------------------------------------------- Defined
    objects = defines(Iterable, doc='''
    @rtype: Iterable(Assemblage)
    The generated assemblages.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='matchersFromData')
class MatchersFromData(HandlerProcessor):
    '''
    The handler that provides the matchers created based on data.
    '''
    
    def __init__(self):
        super().__init__(DataAssemblage=DataAssemblage, DataMatcher=DataMatcher)
        
    def process(self, chain, obtain:Obtain, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populates the assemblages.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        
        if obtain.required != Matcher:
            # The matchers are not required, nothing to do, moving along.
            chain.proceed()
            return
        
        assert isinstance(obtain.assemblages, Iterable), 'Invalid obtain assemblages %s' % obtain.assemblages
    
        objects = self.generate(obtain.assemblages)
        if obtain.objects is None: obtain.objects = objects
        else: obtain.objects = itertools.chain(obtain.objects, objects)
        # We provided the assemblages so we stop the chain.
    
    # ----------------------------------------------------------------
    
    def generate(self, datas):
        '''
        Generates the matchers.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        
        for data in datas:
            assert isinstance(data, DataAssemblage), 'Invalid data %s' % data
            assert isinstance(data.matchers, Iterable), 'Invalid data matchers %s' % data.matchers
            
            for datam in data.matchers:
                assert isinstance(datam, DataMatcher), 'Invalid matcher data %s' % datam
                for model in datam.models:
                    assert isinstance(model, Matcher), 'INvalid matcher model %s' % model
                    yield model
