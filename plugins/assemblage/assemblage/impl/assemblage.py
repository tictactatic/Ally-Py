'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for assemblage data.
'''

from ..api.assemblage import Assemblage, IAssemblageService, Matcher
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
    required = defines(type, doc='''
    @rtype: class
    The required class to be obtained.
    ''')
    assemblageId = defines(int, doc='''
    @rtype: integer
    The assemblage id to filter by.
    ''')
    matcherName = defines(str, doc='''
    @rtype: string
    The matcher name to get the child matchers for.
    ''')
    # ---------------------------------------------------------------- Required
    objects = requires(Iterable)

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
        return self.getObjects(required=Assemblage)
    
    def getMatchers(self, id, name=None):
        '''
        @see: IAssemblageService.getMatchers
        '''
        assert name is None or isinstance(name, str), 'Invalid name %s' % name
        if name is not None: return self.getObjects(assemblageId=id, matcherName=name, required=Matcher)
        return self.getObjects(assemblageId=id, required=Matcher)

    # ----------------------------------------------------------------    
    
    def getObjects(self, **keyargs):
        '''
        Get the objects for the required class.
        '''
        proc = self._processingAssemblages
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        chain = Chain(proc)
        chain.process(**proc.fillIn(obtain=proc.ctx.obtain(**keyargs))).doAll()
        obtain = chain.arg.obtain
        assert isinstance(obtain, Obtain), 'Invalid obtain data %s' % obtain
        if obtain.objects is None: return ()
    
        return obtain.objects
