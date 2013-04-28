'''
Created on Feb 7, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage specification.
'''

# --------------------------------------------------------------------

class RequestNode:
    '''
    Container for an assemblage node request.
    '''
    __slots__ = ('parameters', 'requests')
    
    def __init__(self):
        '''
        Construct the node.
        
        @ivar parameters: list[tuple(string, string)]
            The parameters list of tuples.
        @ivar requests: dictionary{string: RequestNode}
            The sub requests of this request node.
        '''
        self.parameters = []
        self.requests = {}
