'''
Created on Jul 15, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.api.type import Type
from ally.core.spec.transform import ITransfrom
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context

# --------------------------------------------------------------------
# The create contexts.

class RequestEncoder(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(Type, doc='''
    @rtype: Type
    The type that is the target of the encoder create.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(ITransfrom)
    
class RequestEncoderNamed(RequestEncoder):
    '''
    The request create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The name used to render with.
    ''')
    
class DefineEncoder(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(ITransfrom, doc='''
    @rtype: ITransfrom
    The encoder to be used for rendering objects.
    ''')
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    specifiers = optional(list)
    # ---------------------------------------------------------------- Required
    objType = requires(Type)

# --------------------------------------------------------------------

def encoderSpecifiers(context):
    '''
    Provides the specifiers for the provided context.
    
    @param context: Context
        The context with the specifiers to fetch from.
    @return: list|None
        The list of specifiers or None if there is no specifier list available.
    '''
    if DefineEncoder.specifiers in context and context.specifiers: return context.specifiers
    
def encoderName(context, default=None):
    '''
    Provides the name for the provided context.
    
    @param context: Context
        The context with the name to fetch from.
    @return: string|default
        The found name or the provided default value.
    '''
    if DefineEncoder.name in context and context.name: return context.name
    return default
