'''
Created on Jul 10, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the single processing of create decoding requests.
'''

from .base import DefineCreate
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.branch import Branch
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching

# --------------------------------------------------------------------

@injected
class DecodeCreateHandler(HandlerBranching):
    '''
    Implementation for a handler that provides single processing of create decoding create.
    '''
    
    decodeAssembly = Assembly
    # The decode processors to be used for crates decodings.
    
    def __init__(self):
        assert isinstance(self.decodeAssembly, Assembly), 'Invalid decode assembly %s' % self.decodeAssembly
        super().__init__(Branch(self.decodeAssembly).included())

    def process(self, chain, processing, create:DefineCreate, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Provides the create decoding.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, DefineCreate), 'Invalid create %s' % create
        if not create.decodings: return
        
        for decoding in create.decodings: processing.executeWithAll(decoding=decoding, **keyargs)
