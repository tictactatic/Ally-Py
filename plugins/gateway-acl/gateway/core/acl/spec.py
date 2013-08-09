'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications for ACL handling.
'''

import abc

# --------------------------------------------------------------------

class IACLManagement(metaclass=abc.ABCMeta):
    '''
    API that used for fetching the mapped action context for a given action id.
    '''
    
    @abc.abstractmethod
    def get(self, target, **forData):
        '''
        Gets the value for the target based on the provided for data.
        
        @param target: object
            The target to get the value for.
        @param forData: key arguments
            For data key arguments to be used for fetching the names.
        @return: object
            The value for the provided arguments.
        '''
        
    @abc.abstractmethod
    def add(self, target, **data):
        '''
        Adds a new entry for the target using the provided data.
        
        @param target: class
            The target class to fetch the names for.
        @param data: key arguments
            For data key arguments to be used for adding.
        @return: boolean
            True if the adding has been done successfully, False otherwise.
        '''
        
    @abc.abstractmethod
    def remove(self, target, **data):
        '''
        Removes the entry for the target using the provided data.
        
        @param target: class
            The target class to fetch the names for.
        @param data: key arguments
            For data key arguments to be used for removing.
        @return: boolean
            True if the remvoing has been done successfully, False otherwise.
        '''

# --------------------------------------------------------------------
