'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblages for resource data.
'''

from ally.api.config import GET, INSERT
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Invoker, Node
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from ally.http.spec.server import HTTP_GET, HTTP_POST, IEncoderPath
from ally.support.core.util_resources import pathForNode
from assemblage.api.assemblage import Assemblage
from collections import Iterable
import itertools

# --------------------------------------------------------------------

TO_HTTP_METHOD = {GET: HTTP_GET, INSERT: HTTP_POST}
# The mapping from configuration methods to http methods.
                   
# --------------------------------------------------------------------

class DataAssemblageResource(Context):
    '''
    The data assemblage context.
    '''
    # ---------------------------------------------------------------- Required
    id = requires(int)
    node = requires(Node)
    invoker = requires(Invoker)
    
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
    
class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Required
    encoderPath = requires(IEncoderPath)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='assemblagesFromData')
class AssemblagesFromData(HandlerProcessor):
    '''
    The handler that provides the assemblages created based on data.
    '''
        
    def process(self, chain, DataAssemblage:DataAssemblageResource, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populates the assemblages.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert issubclass(DataAssemblage, DataAssemblageResource), 'Invalid data class %s' % DataAssemblage
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        if obtain.required != Assemblage:
            # The assemblages are not required, nothing to do, moving along.
            chain.proceed()
            return
        
        assert isinstance(obtain.assemblages, Iterable), 'Invalid obtain assemblages %s' % obtain.assemblages
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid encoder path %s' % support.encoderPath
    
        objects = self.generate(obtain.assemblages, support.encoderPath)
        if obtain.objects is None: obtain.objects = objects
        else: obtain.objects = itertools.chain(obtain.objects, objects)
        # We provided the assemblages so we stop the chain.
    
    # ----------------------------------------------------------------
    
    def generate(self, datas, encoder):
        '''
        Generates the assemblages.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        assert isinstance(encoder, IEncoderPath), 'Invalid encoder path %s' % encoder
        
        replacer = lambda match, converterPath: '[^\\/]+'
        for data in datas:
            assert isinstance(data, DataAssemblageResource), 'Invalid data %s' % data
            assert isinstance(data.invoker, Invoker), 'Invalid invoker %s' % data.invoker
            
            assemblage = Assemblage()
            assemblage.Id = data.id
            assemblage.Method = TO_HTTP_METHOD[data.invoker.method]
            assemblage.Pattern = encoder.encodePattern(pathForNode(data.node), invalid=replacer, quoted=False)

            yield assemblage
