'''
Created on Jun 30, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the codes to be used for the server responses.
'''

from ally.design.processor.context import Context
from ally.design.processor.attribute import defines

# --------------------------------------------------------------------

class Coded(Context):
    '''
    Context for coded. 
    '''
    # ---------------------------------------------------------------- Defines
    code = defines(str, doc='''
    @rtype: string
    The unique code associated with the context.
    ''')
    isSuccess = defines(bool, doc='''
    @rtype: boolean
    True if the context is in success mode, False otherwise.
    ''')
    
# --------------------------------------------------------------------

class Code:
    '''
    Contains the response code.
    '''
    __slots__ = ('code', 'isSuccess')

    def __init__(self, code, isSuccess):
        '''
        Constructs the code.
        
        @param code: string
            The code text corresponding to this code.
        @param isSuccess: boolean
            Flag indicating if the code is a fail or success code.
        '''
        assert isinstance(code, str), 'Invalid code %s' % code
        assert isinstance(isSuccess, bool), 'Invalid success flag %s' % isSuccess
        self.code = code
        self.isSuccess = isSuccess
        
    def set(self, context):
        '''
        Set the code on the provided context.
        
        @param context: Context
            The context to set the code to.
        '''
        assert isinstance(context, Coded), 'Invalid context %s' % context
        context.code = self.code
        context.isSuccess = self.isSuccess
        
# --------------------------------------------------------------------
# Response codes.

ENCODING_UNKNOWN = Code('Unknown encoding', False)

CONTENT_BAD = Code('Bad content', False)
CONTENT_ILLEGAL = Code('Illegal content', False) #TODO: Gabriel: check if is required to be removed
CONTENT_MISSING = Code('Content missing', False)
CONTENT_EXPECTED = Code('Content stream expected', False)

DECODING_FAILED = Code('Decoding failed', False)
INPUT_ERROR = Code('Input error', False)

DELETE_ERROR = Code('Cannot delete', False)
DELETE_SUCCESS = Code('Successfully deleted', True)

UPDATE_ERROR = Code('Cannot update', False)
UPDATE_SUCCESS = Code('Successfully updated', True)

INSERT_ERROR = Code('Cannot insert', False)
INSERT_SUCCESS = Code('Successfully inserted', True) 

