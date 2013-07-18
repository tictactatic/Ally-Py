'''
Created on Jul 16, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.api.type import Type
from ally.core.spec.transform.encdec import IDecoder, IDevise
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context

# --------------------------------------------------------------------
# The create contexts.

class DefineCreate(Context):
    '''
    The define decode context.
    '''
    # ---------------------------------------------------------------- Required
    decodings = requires(list)

# --------------------------------------------------------------------
# The decoding contexts

class RequestDecoding(Context):
    '''
    The request decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(Type, doc='''
    @rtype: Type
    The type to be decoded.
    ''')
    devise = defines(IDevise, doc='''
    @rtype: IDevise
    The devise used for constructing the decoded object.
    ''')
    # ---------------------------------------------------------------- Required
    decoder = requires(IDecoder)
    
class DefineDecoding(Context):
    '''
    The define decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    decoder = defines(IDecoder, doc='''
    @rtype: IDecoder
    The decoder used for constructing the decoded object.
    ''')
    # ---------------------------------------------------------------- Required
    devise = requires(IDevise)
    type = requires(Type)

# --------------------------------------------------------------------
# The support contexts

class SupportFailure(Context):
    '''
    The decoder failure support context.
    '''
    # ---------------------------------------------------------------- Defined
    failures = defines(list, doc='''
    @rtype: list[tuple(value, Context)]
    The list of decoding failures that occurred, contains tuples having on the first position the value that generated
    the error and on the second position the decoding context that the error occurred on.
    ''')
