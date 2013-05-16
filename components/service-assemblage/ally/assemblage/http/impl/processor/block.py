'''
Created on Apr 12, 2012

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides assemblage markers.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.indexing.spec.model import Block, Perform, Action
from ally.support.http.util_dispatch import RequestDispatch, obtainJSON
from collections import Callable

# --------------------------------------------------------------------

class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    provider = defines(Callable, doc='''
    @rtype: callable(id) -> Block
    The call that provides the block based on the provided id.
    ''')

# --------------------------------------------------------------------

@injected
class BlockHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the markers by using REST data received from either internal or
    external server. The Marker structure is defined as in the @see: assemblage plugin. If there are no markers this
    handler will stop the chain.
    '''
    
    uri = str
    # The URI used in fetching the gateways.
    assembly = Assembly
    # The assembly to be used in processing the request for the gateways.
    
    def __init__(self):
        assert isinstance(self.uri, str), 'Invalid URI %s' % self.uri
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Branch(self.assembly).using('requestCnt', 'response', 'responseCnt', request=RequestDispatch))
        
        self._blocks = {}
        self._actionsByURI = {}
        self._performsByURI = {}

    def process(self, chain, processing, assemblage:Assemblage, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Obtains the markers.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        
        original = assemblage.provider
        def provider(id):
            block = self._obtainBlock(processing, id)
            if block is None and original is not None: return original(id)
            return block
        assemblage.provider = provider
    
    # ----------------------------------------------------------------
    
    def _obtainBlock(self, processing, id):
        '''
        Obtains the block.
        '''
        block = self._blocks.get(id)
        if block is not None: return block
        
        oblock = obtainJSON(processing, self.uri % id)
        if oblock is None: block = None
        else:
            uri = oblock['ActionList']['href']
            oactions = obtainJSON(processing, uri)
            
            actions = []
            if oactions is not None:
                for oaction in oactions['ActionList']:
                    actions.append(self._obtainAction(processing, oaction['href']))
            block = Block(*actions, keys=oblock.get('Keys'))
            
        self._blocks[id] = block
        return block
    
    def _obtainAction(self, processing, uri):
        '''
        Obtains the action.
        '''
        action = self._actionsByURI.get(uri)
        if action is not None: return action
        
        oaction = obtainJSON(processing, uri)
        operforms = obtainJSON(processing, oaction['PerformList']['href'])

        performs = []
        if operforms is not None:
            for operform in operforms['PerformList']:
                performs.append(self._obtainPerform(processing, operform['href']))
            
        action = Action(oaction['Name'], *performs, before=oaction.get('Before'), final=oaction['Final'] == 'True',
                        rewind=oaction['Rewind'] == 'True')
        self._actionsByURI[uri] = action
        return action
    
    def _obtainPerform(self, processing, uri):
        '''
        Obtains the perform.
        '''
        perform = self._performsByURI.get(uri)
        if perform is not None: return perform
        
        operform = obtainJSON(processing, uri)
        
        perform = Perform(operform['Verb'], *operform.get('Flags', ()), index=operform.get('Index'), key=operform.get('Key'),
                          name=operform.get('Name'), value=operform.get('Value'), actions=operform.get('Actions'),
                          escapes=operform.get('Escapes'))
        self._performsByURI[uri] = perform
        return perform
