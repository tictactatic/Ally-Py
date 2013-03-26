'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for assemblage data.
'''

from ..api.assemblage import Assemblage, Matcher, Structure, IAssemblageService
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.exception import InputError

# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    required = defines(object, doc='''
    @rtype: object
    The required object to be obtained.
    ''')
    assemblageId = defines(str, doc='''
    @rtype: string
    The assemblage id to filter by.
    ''')
    structureId = defines(int, doc='''
    @rtype: integer
    The structure id to filter by.
    ''')
    # ---------------------------------------------------------------- Required
    result = requires(object)

# --------------------------------------------------------------------

@injected
@setup(IAssemblageService, name='assemblageService')
class AssemblageService(IAssemblageService):
    '''
    Implementation for @see: IAssemblageService.
    '''
    
    assemblyAssemblages = Assembly; wire.entity('assemblyAssemblages')
    # The assemblage processors to be used for fetching the assemblages.
    
    def __init__(self):
        assert isinstance(self.assemblyAssemblages, Assembly), 'Invalid assemblages assembly %s' % self.assemblyAssemblages
        
        self._processingAssemblages = self.assemblyAssemblages.create(obtain=Obtain)
    
    def getAssemblages(self):
        '''
        @see: IAssemblageService.getAssemblages
        '''
        return self.getResult(True, required=Assemblage)
    
    def getStructure(self, assemblageId, structureId):
        '''
        @see: IAssemblageService.getStructure
        '''
        assert isinstance(assemblageId, str), 'Invalid assemblage id %s' % assemblageId
        assert isinstance(structureId, int), 'Invalid structure id %s' % structureId
        return self.getResult(False, required=Structure, assemblageId=assemblageId, structureId=structureId)
    
    def getStructures(self, assemblageId):
        '''
        @see: IAssemblageService.getStructures
        '''
        assert isinstance(assemblageId, str), 'Invalid assemblage id %s' % assemblageId
        return self.getResult(True, required=Structure.Id, assemblageId=assemblageId)
    
    def getMatchers(self, assemblageId, structureId):
        '''
        @see: IAssemblageService.getMatchers
        '''
        assert isinstance(assemblageId, str), 'Invalid assemblage id %s' % assemblageId
        assert isinstance(structureId, int), 'Invalid structure id %s' % structureId
        return self.getResult(True, required=Matcher, assemblageId=assemblageId, structureId=structureId)
    
    # ----------------------------------------------------------------    
    
    def getResult(self, isIter, **keyargs):
        '''
        Get the result object(s) for the required class.
        '''
        proc = self._processingAssemblages
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        chain = Chain(proc)
        chain.process(**proc.fillIn(obtain=proc.ctx.obtain(**keyargs))).doAll()
        obtain = chain.arg.obtain
        assert isinstance(obtain, Obtain), 'Invalid obtain data %s' % obtain
        if obtain.result is None:
            if isIter: return ()
            else: raise InputError('Unknown id')
    
        return obtain.result
