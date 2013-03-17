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
from .resolvers import copyAttributes, attributesFor, extractContexts, solve, \
    merge, checkIf, reportFor, resolversFor
from .spec import ContextMetaClass, IReport, IProcessor, AssemblyError, \
    LIST_UNAVAILABLE
from .structure import restructureResolvers
import abc

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
    def process(self, sources, processor, resolvers, extensions, report):
        '''
        Process the branch for the current repository.
        
        @param sources: dictionary{string: IResolver}
            The sources resolvers that need to be solved by processors.
        @param processor: dictionary{string: IResolver}
            The resolvers of the processor that handles the branch.
        @param resolvers: dictionary{string: IResolver}
            The resolvers used in creating the final contexts.
        @param extensions: dictionary{string: IResolver}
            The resolvers that are not part of the current resolvers but they are rather extension for the final contexts.
        @param report: IReport
            The report to be used in the registration process.
        @return: Processing
            The branch processing.
        ''' 

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
        
    def process(self, sources, processor, resolvers, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(sources, dict), 'Invalid sources %s' % sources
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Routing \'%s\'' % self.name())
        try:
            rresolvers, rextensions = {}, {}
            calls = self.processAssembly(sources, rresolvers, rextensions, report)
        except: raise AssemblyError('Cannot process Routing for \'%s\'' % self.name())
        
        try:
            solve(rresolvers, processor)
            merge(resolvers, copyAttributes(rresolvers, attributesFor(sources)))
            solve(rresolvers, sources)
            if checkIf(rresolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Routing for \'%s\' has unavailable attributes:%s' % 
                                    (self.name(), reportFor(rresolvers, LIST_UNAVAILABLE)))
            solve(rresolvers, rextensions)
            if self.merged:
                assert isinstance(extensions, dict), 'Invalid extensions %s' % extensions
                merge(extensions, rresolvers)
                return Processing(calls)
            
            report.add(rresolvers)
            return Processing(calls, create(rresolvers))
        except AssemblyError: raise
        except:
            raise AssemblyError('Resolvers problems on Routing for \'%s\'\n, with resolvers:%s\n'
                                ', and extensions:%s' % (self.name(), reportFor(rresolvers), reportFor(rextensions)))
            
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
        
        @param current: arguments[string|tuple(string, string)]
            The current contexts names to be used from the ongoing process, or mappings that the using needs to make,
            attention the order in which the context mappings are provided
            is crucial, examples:
                ('request': 'solicitation')
                    The wrapped branch will receive as the 'request' context the 'solicitation' context.
                ('request': 'solicitation'), ('request': 'response')
                    The wrapped branch will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation': 'request'), ('response': 'request')
                    The wrapped branch will receive as the 'solicitation' and 'response' context the 'request' context.
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be solved by the used container.
        '''
        if __debug__:
            for name in current: assert isinstance(name, (str, tuple)), 'Invalid current context name %s' % name
            assert len(set(current)) == len(current), 'Cannot have duplicated current names'
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        super().__init__(assembly)
        
        self.current = current
        self.contexts = contexts
    
    def process(self, sources, processor, resolvers, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        merge(resolvers, processor)
        report = report.open('Using \'%s\'' % self.name())
        try:
            if self.current: usources = merge(restructureResolvers(resolvers, self.current), self.contexts)
            else: usources = resolversFor(self.contexts)
            
            uextensions, uresolvers = {}, {}
            calls = self.processAssembly(usources, uresolvers, uextensions, report)
                    
        except: raise AssemblyError('Cannot process Using for \'%s\'' % self.name())
        
        try:
            solve(uresolvers, usources, False)
            #TODO: Gabriel check the reported unused for REST
            #if self.current: solve(uresolvers, restructureResolvers(sources, self.current), False)
            if checkIf(uresolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Using for \'%s\' has unavailable attributes:%s' % 
                                    (self.name(), reportFor(uresolvers, LIST_UNAVAILABLE)))
            solve(uresolvers, uextensions)
            if self.current:
                uextensions = restructureResolvers(uresolvers, self.current, True)
                uextensions = copyAttributes(uextensions, attributesFor(resolvers))
                merge(extensions, uextensions)
            report.add(uresolvers)
            return Processing(calls, create(uresolvers))
        except AssemblyError: raise
        except:
            raise AssemblyError('Resolvers problems on Using for \'%s\'\n, with sources:%s\n, with processors:%s\n'
                    ', and extensions:%s' % (self.name(), reportFor(usources), reportFor(uresolvers), reportFor(uextensions)))

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
    
    def process(self, sources, processor, resolvers, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Included \'%s\'' % self.name())
        try:
            iresolvers, iextensions = {}, {}
            calls = self.processAssembly(sources, iresolvers, iextensions, report)
            
            if self.using:
                uresolvers = extractContexts(iresolvers, self.using)
                uresolvers = solve(uresolvers, self.using)
                if checkIf(uresolvers, LIST_UNAVAILABLE):
                    raise AssemblyError('Included for \'%s\' has unavailable attributes:%s' % 
                                        (self.name(), reportFor(uresolvers, LIST_UNAVAILABLE)))
                solve(uresolvers, extractContexts(iextensions, self.using))
                
                report.add(uresolvers)
                contexts = create(uresolvers)
            else: contexts = None
            
            merge(resolvers, solve(iresolvers, processor))
            solve(extensions, iextensions)
            return Processing(calls, contexts)
        
        except: raise AssemblyError('Cannot process Included for \'%s\'' % self.name())
