'''
Created on Jun 4, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides server specification.
'''

import abc

# --------------------------------------------------------------------

class IEncoderPathInvoker(metaclass=abc.ABCMeta):
    '''
    Provides the invoker path encoding.
    '''
    __slots__ = ()

    @abc.abstractmethod
    def encode(self, invoker, values=None, quoted=True):
        '''
        Encodes the provided invoker to a full request path.
        
        @param invoker: Context
            The invoker context to have the path encoded.
        @param values: dictionary{TypeProperty: object}|None
            A dictionary containing the path values indexed by the node properties, if a value is string it will be used as it
            is and no actual conversion will be attempted.
        @param quoted: boolean
            Flag indicating that the encoded values should be quoted.
        @return: string
            The full compiled path.
        '''
    
    @abc.abstractmethod
    def encodePattern(self, invoker, values=None):
        '''
        Encodes the provided invoker to a pattern path that can be used as regex to identify paths corresponding to the provided
        invoker.
        
        @param invoker: Context
            The invoker context to have the path encoded.
        @param values: dictionary{TypeProperty: object}|None
            A dictionary containing the path values indexed by the node properties, if a value is string it will be used as it
            is and no actual conversion will be attempted.
        @return: string
            The path pattern.
        '''
