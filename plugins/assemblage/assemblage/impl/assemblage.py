'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for assemblage data.
'''

from ..api.assemblage import IAssemblageService
from ally.container.ioc import injected

# --------------------------------------------------------------------

@injected
class AssemblageService(IAssemblageService):
    '''
    Implementation for @see: IAssemblageService based on ally core component resources.
    '''
    
    def __init__(self):
        pass
    
    def getIdentifiers(self):
        '''
        @see: IAssemblageService.getIdentifiers
        '''
    
    def getAssemblages(self, id):
        '''
        @see: IAssemblageService.getAssemblages
        '''
    
    def getChildAssemblages(self, id):
        '''
        @see: IAssemblageService.getChildAssemblages
        '''
        
    def getMatchers(self, id):
        '''
        @see: IAssemblageService.getMatchers
        '''
    
    def getAdjusters(self, id):
        '''
        @see: IAssemblageService.getAdjusters
        '''
    
    def getFailedReplacers(self, id):
        '''
        @see: IAssemblageService.getFailedReplacers
        '''
