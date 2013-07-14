'''
Created on Jul 13, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definitions setups.
'''

from ally.container import ioc
from ally.core.impl.verifier import IVerifier

# --------------------------------------------------------------------

@ioc.entity
def definitions():
    ''' The general definitions data'''
    return []

@ioc.entity
def definitionError():
    ''' The dictionary containing the error code to definition verifier list'''
    return {}

@ioc.entity
def definitionDescribers():
    ''' The describers used for definitions'''
    return []

# --------------------------------------------------------------------

def addDefinition(**data):
    '''
    Adds a new definition data.
    !Attention, this is only available for setup functions!
    
    @param data: key arguments
        The data to add.
    '''
    definitions().append(data)

def addError(code, *verifiers):
    '''
    Adds definition error verifiers.
    !Attention, this is only available for setup functions!
    
    @param code: string
        The error code to map the verifiers to.
    @param verifiers: arguments[IVerifier]
        The verifiers for the error definitions.
    '''
    assert isinstance(code, str), 'Invalid code %s' % code
    assert verifiers, 'At least one verifier is required'
    if __debug__:
        for verifier in verifiers: assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
        
    present = definitionError().get(code)
    if present is None: present = definitionError()[code] = []
    present.extend(verifiers)

def addDescriber(verifier, *messages):
    '''
    Adds a new definition describer.
    !Attention, this is only available for setup functions!
    
    @param verifier: IVerifier
        The verifier to be used for associating the messages.
    @param messages: arguments[string]
        The message(s) for the verifier.
    '''
    assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
    assert messages, 'At least one message is required'
    if __debug__:
        for message in messages: assert isinstance(message, str), 'Invalid message %s' % message
        
    definitionDescribers().append((verifier,) + messages)