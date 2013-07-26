'''
Created on Jul 26, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for parameter decoding.
'''

from ally.api.type import Input
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import findFirst
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    decodingsParameter = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The decoding dictionary to be used in decoding the parameters values.
    ''')

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    # ---------------------------------------------------------------- Required
    input = requires(Input)
    doDecode = requires(IDo)
      
class Parameter(Context):
    '''
    The parameter context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)

# --------------------------------------------------------------------

@injected
class IndexParameterHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the indexing for parameter decoding.
    '''
    
    separator = '.'
    # The separator to use for parameter names.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__()
        
    def process(self, chain, decoding:Decoding, parameter:Parameter, invoker:Invoker, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Indexed the parameter decodings.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(parameter, Parameter), 'Invalid parameter %s' % parameter
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        if not decoding.doDecode: return
        name = self.separator.join(parameter.path)
        
        if invoker.decodingsParameter is None: invoker.decodingsParameter = {}
        if name in invoker.decodingsParameter:
            log.error('Cannot use because there is the parameters for \'%s\' and \'%s\' have the same path \'%s\'',
                      findFirst(decoding, Decoding.parent, Decoding.input) or name,
                      findFirst(invoker.decodingsParameter[name], Decoding.parent, Decoding.input) or name, name)
            raise Abort(decoding)
        invoker.decodingsParameter[name] = decoding
