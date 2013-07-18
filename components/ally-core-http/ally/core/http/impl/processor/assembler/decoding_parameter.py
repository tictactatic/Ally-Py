'''
Created on Jul 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker parameters decoder.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.assembler.decoding_base import Invoker, \
    DecodingBase, DecodingBaseHandler
from ally.design.processor.attribute import defines
from ally.support.util_context import findFirst
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

CATEGORY_PARAMETER = 'parameter'
# The name of the parameters category.

# --------------------------------------------------------------------

class InvokerParameter(Invoker):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    definitions = defines(list, doc='''
    @rtype: list[Context]
    Definitions containing representative data for invoker decoders.
    ''')
    decodingParameters = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The decoding dictionary to be used in decoding the parameters values.
    ''')
    
class DefinitionParameter(DecodingBase):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    category = defines(str, doc='''
    @rtype: string
    The decoding category name.
    ''')
    name = defines(str, doc='''
    @rtype: string
    The decoding name.
    ''')
    
# --------------------------------------------------------------------

@injected
class DecodingParameterHandler(DecodingBaseHandler):
    '''
    Base implementation for a handler that provides the parameter decoders for invokers.
    '''
    
    separator = '.'
    # The separator to use for parameter names.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(('Support', 'SupportDecodeParameter'), Definition=DefinitionParameter, Invoker=InvokerParameter)
    
    def index(self, invoker, decodings):
        '''
        @see: DecodingBaseHandler.index
        '''
        assert isinstance(invoker, InvokerParameter), 'Invalid invoker %s' % invoker
        
        pathsFor, decodingByPath = {}, {}
        for decoding in decodings:
            assert isinstance(decoding, DefinitionParameter), 'Invalid decoding %s' % decoding
            path = self.separator.join(decoding.path)
            pathFor = findFirst(decoding, DecodingBase.parent, DecodingBase.input) or path
            if path in pathsFor:
                log.error('Cannot use because there is the parameters for \'%s\' and \'%s\' have the same path \'%s\', at:%s',
                          pathFor, pathsFor[path], path, invoker.location)
                return
            decodingByPath[path] = decoding
            pathsFor[path] = pathFor
            
            decoding.category = CATEGORY_PARAMETER
            decoding.name = path
            
            if invoker.definitions is None: invoker.definitions = []
            invoker.definitions.append(decoding)
            
        if invoker.decodingParameters is None: invoker.decodingParameters = decodingByPath
        else: invoker.decodingParameters.update(decodingByPath)
        
        return True
