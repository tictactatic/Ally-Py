'''
Created on Jul 13, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definitions setups.
'''

from ally.container import ioc
from ally.core.spec.definition import IVerifier

# --------------------------------------------------------------------

INFO_LIST_ITEM = 'list_item'
# The index for list item info.

# --------------------------------------------------------------------

@ioc.entity
def categories():
    ''' The categories descriptions, contains dictionary{string: list[string]}'''
    return {}

@ioc.entity
def definitions():
    ''' The general definitions data, contains dictionary{string: object}'''
    return []

@ioc.entity
def errors():
    ''' The list containing the error code to definition verifier list, contains tuple(string, IVerifier, tuple(string)|None)'''
    return []

@ioc.entity
def descriptions():
    ''' The descriptions used for definitions, contains tuple(IVerifier, list[string], dictionary{string: object})'''
    return []

# --------------------------------------------------------------------

def category(category, *descriptions):
    '''
    Adds a new category description(s).
    !Attention, this is only available for setup functions!
    
    @param category: string
        The category to add the description for.
    @param descriptions: arguments[string]
        The description(s) to add for the category.
    '''
    assert isinstance(category, str), 'Invalid category %s' % category
    assert descriptions, 'At least one description is required'
    if __debug__:
        for desc in descriptions: assert isinstance(desc, str), 'Invalid description %s' % desc
    descs = categories().get(category)
    if descs is None: descs = categories()[category] = []
    descs.extend(descriptions)

def defin(**data):
    '''
    Adds a new definition data.
    !Attention, this is only available for setup functions!
    
    @param data: key arguments
        The data to add.
    '''
    definitions().append(data)

def error(code, verifier, *messages):
    '''
    Adds definition error verifiers.
    !Attention, this is only available for setup functions!
    
    @param code: string
        The error code to map the verifiers to.
    @param verifier: IVerifier
        The verifier for the error definitions.
    @param messages: arguments[string]
        The error(s) messages for the error definitions, all provided verifiers need to check in order to associate
        the definition with the error.
    '''
    assert isinstance(code, str), 'Invalid code %s' % code
    assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
    assert messages, 'At least one message is required'
    if __debug__:
        for message in messages: assert isinstance(message, str), 'Invalid message %s' % message
        
    errors().append((code, verifier, messages))

def desc(verifier, *messages, **data):
    '''
    Adds a new definition description.
    !Attention, this is only available for setup functions!
    
    @param items: arguments[IVerifier|string]
        The definition(s) verifier(s) that are used to associate the description with a definition,
        or description message(s) to be displayed, all provided verifiers need to check in order to associate
        the description message.
    @param data: key arguments
        Data used for the place holders in the messages.
    '''
    assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
    assert messages, 'At least one message is required'
    if __debug__:
        for message in messages: assert isinstance(message, str), 'Invalid message %s' % message
        
    descriptions().append((verifier, messages, data))
