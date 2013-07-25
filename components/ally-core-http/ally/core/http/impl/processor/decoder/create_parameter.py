'''
Created on Jul 19, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the decoded creation for parameters.
'''

from ally.api.type import Input
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Create(Context):
    '''
    The define decode context.
    '''
    # ---------------------------------------------------------------- Required
    decodings = requires(list)

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    input = requires(Input)

class Parameter(Context):
    '''
    The parameter context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list, doc='''
    @rtype: list[string]
    The path used for the parameter name.
    ''')
    
# --------------------------------------------------------------------

@injected
class CreateParameterDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the create of decoded parameters.
    '''
    
    decodeParameterAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodeParameterAssembly, Assembly), \
        'Invalid parameter decode assembly %s' % self.decodeParameterAssembly
        super().__init__(Branch(self.decodeParameterAssembly).using(parameter=Parameter).
                         included(('Support', 'SupportDecodeParameter'), ('decoding', 'Decoding')).included(),
                         Decoding=Decoding)
    
    def process(self, chain, processing, create:Create, **keyargs):
        '''
        HandlerBranching.process
        
        Process the parameter decoding.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, Create), 'Invalid create %s' % create
        if not create.decodings: return
        
        for decoding in create.decodings:
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            if decoding.doDecode or not decoding.input: continue
            
            assert isinstance(decoding.input, Input), 'Invalid input %s' % input
            processing.wingIn(chain, True, decoding=decoding,
                              parameter=processing.ctx.parameter(path=[decoding.input.name]))
