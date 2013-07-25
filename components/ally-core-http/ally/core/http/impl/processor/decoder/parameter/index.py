'''
Created on Jul 24, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for parameter decoding.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.decoder.general import index
from ally.core.impl.processor.decoder.general.index import IndexDecode
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.support.util_context import findFirst
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(index.Invoker):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    decodingsParameter = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The decoding dictionary to be used in decoding the parameters values.
    ''')
    
class Parameter(Context):
    '''
    The parameter context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)

class Decoding(index.Decoding):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    parameterDefinition = defines(Context, doc='''
    @rtype: Context
    The definition context for the parameter decoding.
    ''')
      
class Definition(index.DefinitionDecoding):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The definition name.
    ''')

# --------------------------------------------------------------------

@injected
class IndexParameterDecode(IndexDecode):
    '''
    Implementation for a handler that provides the indexing for parameter decoding.
    '''
    
    separator = '.'
    # The separator to use for parameter names.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(decoding=Decoding, invoker=Invoker, Definition=Definition)
        
    def process(self, chain, decoding:Context, parameter:Parameter, invoker:Context, **keyargs):
        '''
        @see: IndexDecode.process
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(parameter, Parameter), 'Invalid parameter %s' % parameter
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        if decoding.doDecode:
            name = self.separator.join(parameter.path)
            
            if invoker.decodingsParameter is None: invoker.decodingsParameter = {}
            if name in invoker.decodingsParameter:
                log.error('Cannot use because there is the parameters for \'%s\' and \'%s\' have the same path \'%s\'',
                          findFirst(decoding, Decoding.parent, Decoding.input) or name,
                          findFirst(invoker.decodingsParameter[name], Decoding.parent, Decoding.input) or name, name)
                raise Abort(decoding)
            invoker.decodingsParameter[name] = decoding
            
            super().process(chain, decoding=decoding, parameter=parameter, invoker=invoker, **keyargs)
        
    # ----------------------------------------------------------------
    
    def processDefinition(self, decoding, parameter, **keyargs):
        '''
        @see: IndexDecode.processDefinition
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(parameter, Parameter), 'Invalid parameter %s' % parameter
        
        keyargs.update(decoding=decoding, parameter=parameter, definition=decoding.parameterDefinition)
        decoding.parameterDefinition = super().processDefinition(**keyargs)
        assert isinstance(decoding.parameterDefinition, Definition), 'Invalid definition %s' % decoding.parameterDefinition
        decoding.parameterDefinition.name = self.separator.join(parameter.path)
        
        return decoding.parameterDefinition
