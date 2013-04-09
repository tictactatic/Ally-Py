'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.assemblage.http.spec.assemblage import RequestNode
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_io import IInputStream
from collections import Callable, Iterable
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(Iterable, doc='''
    @rtype: Iterable
    The assembled content source.
    ''')
    # ---------------------------------------------------------------- Required
    requestNode = requires(RequestNode)
    requestHandler = requires(Callable)
    main = requires(object)

class Content(Context):
    '''
    The assemblage content context.
    '''
    # ---------------------------------------------------------------- Required
    errorStatus = requires(int)
    errorText = requires(str)
    source = requires(IInputStream)
    transcode = requires(Callable)
    indexes = requires(list)
    
# --------------------------------------------------------------------

@injected
class AssemblerHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the assembling.
    '''
    
    def __init__(self):
        super().__init__(Content=Content)

    def process(self, chain, assemblage:Assemblage, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Assemble response content.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(assemblage.main, Content), 'Invalid main content %s' % assemblage.main
        assert assemblage.main.errorStatus is None, 'Invalid main content %s, has an error status' % assemblage.main
        
        if assemblage.main.indexes is None: return  # No indexes to process
        
        
