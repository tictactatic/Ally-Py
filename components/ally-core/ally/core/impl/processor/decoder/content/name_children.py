'''
Created on Jul 26, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the name and adding as a child for decodings.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The name of the decode.
    ''')
    children = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The decoding children indexed by the decoding name.
    ''')
    # ---------------------------------------------------------------- Required
    parent = requires(Context)

# --------------------------------------------------------------------
 
@injected
class NameChildrenHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the naming of the decoding and adding as a child to
    the parent based on that name.
    '''
    
    name = str
    # The name to place on the decoding.
    
    def __init__(self):
        assert isinstance(self.name, str), 'Invalid name %s' % self.name
        super().__init__()

    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the named decoder.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(decoding.parent, Decoding), 'Invalid decoding %s' % decoding.parent
        
        decoding.name = self.name
        if decoding.parent.children is None: decoding.parent.children = {}
        decoding.parent.children[self.name] = decoding
