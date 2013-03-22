'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for assemblage data.
'''

from ..api.assemblage import IAssemblageService
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from collections import Iterable

# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    doAssemblages = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that the assemblages have to be created.
    ''')
    # ---------------------------------------------------------------- Required
    assemblages = requires(Iterable)

# --------------------------------------------------------------------

@injected
@setup(IAssemblageService, name='assemblageService')
class AssemblageService(IAssemblageService):
    '''
    Implementation for @see: IAssemblageService.
    '''
    
    assemblagesAssembly = Assembly; wire.entity('assemblagesAssembly')
    # The assemblage processors to be used for fetching the assemblages.
    
    def __init__(self):
        assert isinstance(self.assemblagesAssembly, Assembly), 'Invalid assemblages assembly %s' % self.assemblagesAssembly
        
        self._processingAssemblages = self.assemblagesAssembly.create(obtain=Obtain)
    
    def getAssemblages(self):
        '''
        @see: IAssemblageService.getAssemblages
        '''
        proc = self._processingAssemblages
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        chain = Chain(proc)
        chain.process(**proc.fillIn(obtain=proc.ctx.obtain(doAssemblages=True))).doAll()
        obtain = chain.arg.obtain
        assert isinstance(obtain, Obtain), 'Invalid obtain data %s' % obtain
        if obtain.assemblages is None: return ()
        
        return obtain.assemblages
    
    def getTargets(self, id):
        '''
        @see: IAssemblageService.getTargets
        '''
    
    def getChildTargets(self, id):
        '''
        @see: IAssemblageService.getChildTargets
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
        
