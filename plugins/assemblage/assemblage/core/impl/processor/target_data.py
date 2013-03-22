'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the target data based on representation objects.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Invoker, Node, Path
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import Handler, HandlerBranchingProceed, \
    HandlerProcessorProceed
from ally.support.core.util_resources import pathForNode
from collections import Iterable
import logging
from ally.core.spec.transform.representation import Object, Collection
from assemblage.api.assemblage import Target, Matcher, Adjuster
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------
    
class DataTarget(Context):
    '''
    The data context.
    '''
    # ---------------------------------------------------------------- Defined
    targets = defines(dict, doc='''
    @rtype: dictionary{string: object}
    The target objects representations.
    ''')
    # ---------------------------------------------------------------- Required
    representation = requires(object)
    
class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Required
    datas = requires(Iterable)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideTargets')
class ProvideTargets(HandlerProcessorProceed):
    '''
    Provides the target data.
    '''
    
    def process(self, Data:DataTarget, obtain:Obtain, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the target data
        '''
        assert issubclass(Data, DataTarget), 'Invalid data class %s' % Data
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(obtain.datas, Iterable), 'Invalid datas %s' % obtain.datas
        
        if obtain.required not in (Target, Matcher, Adjuster): return  # The required type doesn't need targets 
        
        obtain.datas = self.populateTargets(obtain.datas)
        
    # ----------------------------------------------------------------
        
    def populateTargets(self, datas):
        '''
        Provides the representation data.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        for data in datas:
            assert isinstance(data, DataTarget), 'Invalid data %s' % data
            
            if isinstance(data.representation, Object):
                pass
            elif isinstance(data.representation, Collection):
                pass
            else:
                log.error('Cannot provide targets for representation %s', data.representation)
                continue
            
            data.targets = {}
            yield data
