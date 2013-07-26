'''
Created on Jul 26, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Populates the mandatory flag on the decoding.
'''

from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    isMandatory = defines(bool, doc='''
    @rtype: boolean
    Indicates that the decoding needs to have a value provided.
    ''')

# --------------------------------------------------------------------

class MandatorySetHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the mandatory flag set.
    '''

    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the mandaotyr flag.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        decoding.isMandatory = True
