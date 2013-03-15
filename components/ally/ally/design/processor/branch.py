'''
Created on Mar 14, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing processors branches.
'''

from .assembly import Assembly
from .context import create
from .execution import Processing
from .repository import Repository, RepositoryUsed
from .spec import ContextMetaClass, IRepository, IReport, IProcessor, \
    AssemblyError
from .support.util_repository import hasUnavailable, reportUnavailable
import abc
from .manipulator import Mapping

# --------------------------------------------------------------------

class IBranch(metaclass=abc.ABCMeta):
    '''
    Specification for a branch handler.
    '''
    
    @abc.abstractmethod
    def name(self):
        '''
        Provides the name of the branch.
        '''
    
    @abc.abstractmethod
    def process(self, processor, sources, current, extensions, report):
        '''
        Process the branch for the current repository.
        
        @param processor: IRepository
            The contexts resolvers repository of the processor that handles the branch..
        @param sources: IRepository
            The sources resolvers repository that need to be solved by processors.
        @param current: IRepository
            The current resolvers repository solved so far by processors.
        @param extensions: IRepository
            The resolvers repository that are not part of the main stream resolvers but they are rather extension for 
            the created contexts.
        @param report: IReport
            The report to be used in the registration process.
        @return: Processing
            The branch processing.
        ''' 
# --------------------------------------------------------------------

class WithAssembly(IBranch):
    '''
    Branch for implementation that provides assembly support.
    '''

    def __init__(self, assembly):
        '''
        Construct the branch with target.
        
        @param assembly: Assembly
            The target assembly or branch to use.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        self.assembly = assembly
        
    def name(self):
        '''
        @see: IBranch.name
        '''
        return self.assembly.name
    
    # ----------------------------------------------------------------
    
    def processAssembly(self, sources, current, extensions, report):
        '''
        Process the assembly.
        
        @return: list[Callable]
            Returns the processed target calls.
        '''
        calls = []
        for proc in self.assembly.processors:
            assert isinstance(proc, IProcessor), 'Invalid processor %s' % proc
            proc.register(sources, current, extensions, calls, report)
        return calls

class WithBranch(IBranch):
    '''
    Branch for implementation that provides a wrapped branch support.
    '''

    def __init__(self, branch):
        '''
        Construct the branch with target.
        
        @param branch: IBranch
            The target branch to use.
        '''
        assert isinstance(branch, IBranch), 'Invalid branch %s' % branch
        self.branch = branch
        
    def name(self):
        '''
        @see: IBranch.name
        '''
        return self.branch.name()

# --------------------------------------------------------------------

class Routing(WithAssembly):
    '''
    Branch for routed processors containers. By routing is understood that the processors will be executed separately
    from the main chain and they need to solve the main contexts. 
    '''
    
    def __init__(self, assembly, merged=True):
        '''
        Construct the routing branch.
        @see: WithAssembly.__init__
        
        @param merged: boolean
            Flag indicating that the routing should be merged with the main context, thus allowing the routing processor
            to use the same objects.
            Attention if this is true then no processing context will be available.
        '''
        assert isinstance(merged, bool), 'Invalid merged flag %s' % merged
        super().__init__(assembly)
        
        self.merged = merged
        
    def process(self, processor, sources, current, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(sources, IRepository), 'Invalid sources %s' % sources
        assert isinstance(current, IRepository), 'Invalid current repository %s' % current
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Routing \'%s\'' % self.name())
        try:
            rcurrent, rextensions = Repository(), Repository()
            calls = self.processAssembly(sources, rcurrent, rextensions, report)
        except: raise AssemblyError('Cannot process Routing for \'%s\'' % self.name())
        
        try:
            rcurrent.solve(processor)
            current.merge(rcurrent.copy(sources.listAttributes()))
            rcurrent.solve(sources)
            if hasUnavailable(rcurrent):
                raise AssemblyError('Routing for \'%s\' has unavailable attributes:\n%s' % 
                                    (self.name(), reportUnavailable(rcurrent)))
            rcurrent.solve(rextensions)
            
            if self.merged:
                assert isinstance(extensions, IRepository), 'Invalid extensions %s' % extensions
                extensions.merge(rcurrent)
                return Processing(calls)
            
            report.add(rcurrent)
            return Processing(calls, create(rcurrent))
        except AssemblyError: raise
        except:
            raise AssemblyError('Resolvers problems on Routing for \'%s\'\n, with resolvers %s\n'
                                ', and extensions %s' % (self.name(), rcurrent, rextensions))
            
class Using(WithAssembly):
    '''
    Branch for using processors containers. By using is understood that the processors will be executed separately
    from the main chain and they need to solve the provided contexts. 
    '''

    def __init__(self, assembly, *current, **contexts):
        '''
        Construct the using branch. All the contexts that are not declared will be considered included contexts and thus
        they will not have a processing context class.
        @see: WithAssembly.__init__
        
        @param current: arguments[string]
            The current contexts names to be used from the ongoing process.
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be solved by the used container.
        '''
        if __debug__:
            for name in current: assert isinstance(name, str), 'Invalid current context name %s' % name
            assert len(set(current)) == len(current), 'Cannot have duplicated current names'
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        super().__init__(assembly)
        
        self.current = current
        self.contexts = contexts
    
    def process(self, processor, sources, current, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(sources, IRepository), 'Invalid sources %s' % sources
        assert isinstance(current, IRepository), 'Invalid current repository %s' % current
        assert isinstance(extensions, IRepository), 'Invalid extensions %s' % extensions
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        current.merge(processor)
        report = report.open('Using \'%s\'' % self.name())
        try:
            if self.current:
                usources = sources.copy(self.current)
                ucurrent = current.copy(self.current)
                usources.merge(self.contexts)
            else:
                usources = Repository(self.contexts)
                ucurrent = Repository()
            
            uextensions = Repository()
            calls = self.processAssembly(usources, ucurrent, uextensions, report)
                    
        except: raise AssemblyError('Cannot process Using for \'%s\'' % self.name())
        
        try:
            ucurrent.solve(usources)
            if hasUnavailable(ucurrent):
                raise AssemblyError('Using for \'%s\' has unavailable attributes:\n%s' % 
                                    (self.name(), reportUnavailable(ucurrent)))
            ucurrent.solve(uextensions)
            if self.current: extensions.merge(ucurrent.copy(self.current).copy(current.listAttributes()))
            
            report.add(ucurrent)
            return Processing(calls, create(ucurrent))
        except AssemblyError: raise
        except:
            raise AssemblyError('Resolvers problems on Using for \'%s\'\n, with sources %s\n, with processors %s\n'
                                ', and extensions %s' % (self.name(), usources, ucurrent, uextensions))

class Included(WithAssembly):
    '''
    Branch for included processors containers. By included is understood that the processors will be executed using the
    main context objects, so basically is like having included also the processors in the main chain but still have control
    over when and how they are executed.
    '''
    
    def __init__(self, assembly, **using):
        '''
        Construct the included branch.
        @see: WithAssembly.__init__
        
        @param using: key arguments{string, ContextMetaClass}
            The contexts to be used rather then included.
        '''
        super().__init__(assembly)
        if __debug__:
            for name, clazz in using.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        self.using = using
    
    def process(self, processor, sources, current, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(current, IRepository), 'Invalid current repository %s' % current
        assert isinstance(extensions, IRepository), 'Invalid extensions %s' % extensions
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Included \'%s\'' % self.name())
        
        try:
            icurrent, iextensions = Repository(), Repository()
            calls = self.processAssembly(sources, icurrent, iextensions, report)
            
            if self.using:
                ucurrent = icurrent.extract(self.using)
                assert isinstance(ucurrent, IRepository)
                ucurrent.solve(self.using)
                if hasUnavailable(ucurrent):
                    raise AssemblyError('Included for \'%s\' has unavailable attributes:\n%s' % 
                                        (self.name(), reportUnavailable(ucurrent)))
                ucurrent.solve(iextensions.extract(self.using))
                
                report.add(ucurrent)
                contexts = create(ucurrent)
            else: contexts = None
            
            icurrent.solve(processor)
            current.merge(icurrent)
            extensions.solve(iextensions)
            return Processing(calls, contexts)
        
        except: raise AssemblyError('Cannot process Included for \'%s\'' % self.name())

# --------------------------------------------------------------------

class Combine(WithBranch):
    '''
    Branch wrapper for combining contexts
    '''
    
    def __init__(self, branch, *mapping):
        '''
        Construct the combining branch.
        @see: WithBranch.__init__
        
        @param mapping: arguments[tuple(string string)]
            The mappings that the combine needs to make, attention the order in which the context mappings are provided
            is crucial, examples:
                ('request': 'solicitation')
                    The wrapped branch will receive as the 'request' context the 'solicitation' context.
                ('request': 'solicitation'), ('request': 'response')
                    The wrapped branch will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation': 'request'), ('response': 'request')
                    The wrapped branch will receive as the 'solicitation' and 'response' context the 'request' context.
        '''
        assert mapping, 'At least one mapping is required'
        super().__init__(branch)
        
        self.mapping = Mapping()
        for first, second in mapping: self.mapping.map(first, second)
        
    def process(self, processor, sources, current, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, IRepository), 'Invalid processor %s' % processor
        assert isinstance(current, IRepository), 'Invalid current repository %s' % current
        assert isinstance(extensions, IRepository), 'Invalid extensions %s' % extensions
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        current.merge(processor)
        
        wprocessor = RepositoryUsed(self.mapping.structure(processor))
        wsources = RepositoryUsed(self.mapping.structure(sources))
        wcurrent = RepositoryUsed(self.mapping.structure(current))
        wextensions = RepositoryUsed(self.mapping.structure(extensions))
        
        processing = self.branch.process(wprocessor, wsources, wcurrent, wextensions, report)
        
        self.mapping.restructure(current, wcurrent)
        self.mapping.restructure(extensions, wextensions)
        
        return processing
