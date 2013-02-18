'''
Created on Jan 21, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications for ACL gateway support.
'''

import abc

# --------------------------------------------------------------------

class IAuthenticatedProvider(metaclass=abc.ABCMeta):
    '''
    API for gateways authenticated values provider.
    '''
    
    @abc.abstractmethod
    def valueFor(self, propertyType):
        '''
        Requests the authenticated value for the provided property type.
        
        @param propertyType: TypeProperty
            The property type to provide the value for.
        @return: string|None
            The authenticated value for the property type or None if there is no such value.
        '''

class IGatewayAclService(metaclass=abc.ABCMeta):
    '''
    API for gateway ACL model service.
    '''
    
    @abc.abstractmethod
    def gatewaysFor(self, rights, provider, root='%s'):
        '''
        Provides the gateway objects compiled for the provided right or rights.
        
        @param rights: Iterable(RightBase)|RightBase
            The rights to construct gateway for.
        @param provider: IAuthenticatedProvider
            The @see: IAuthenticatedProvider used in solving the filters paths.
        @param root: string
            The root URI string to use on the patterns and filters paths, the root needs to contain the place 
            holder '%s' where to place the pattern or filter. For patterns the root will be escaped automatically.
        @return: list[Gateway]
            The list of gateways models reflecting the provided rights.
        '''
