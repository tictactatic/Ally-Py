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
    merge, checkIf, reportFor
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
    def process(self, sources, resolvers, extensions, report):
        '''
        Process the branch for the current repository.
        
        @param sources: dictionary{string: IResolver}
            The sources resolvers that need to be solved by processors.
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
        Construct the branch with target assembly.
        
        @param assembly: Assembly
            The target assembly to use.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        self._assembly = assembly
        
    def name(self):
        '''
        @see: IBranch.name
        '''
        return self._assembly.name
    
    # ----------------------------------------------------------------
    
    def _processAssembly(self, sources, current, extensions, report):
        '''
        Process the assembly.
        
        @return: list[Callable]
            Returns the processed target calls.
        '''
        calls = []
        for proc in self._assembly.processors:
            assert isinstance(proc, IProcessor), 'Invalid processor %s' % proc
            proc.register(sources, current, extensions, calls, report)
        return calls

# --------------------------------------------------------------------

class Routing(WithAssembly):
    '''
    Branch for routed processors containers. By routing is understood that the processors will be executed separately
    from the main chain and they need to solve the main contexts, the routing processor uses the same contexts.
    '''
    
    def __init__(self, assembly):
        '''
        Construct the routing branch.
        @see: WithAssembly.__init__
        '''
        super().__init__(assembly)
        
        self._usingContexts = {}
        self._usingNames = set()
        
    def using(self, *names, **contexts):
        '''
        Register the context names required for using, basically the contexts that need to be present on the processing.
        
        @param names: arguments[string]
            The contexts names to be used rather then routed.
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be used rather then routed.
        @return: self
            This branch for chaining purposes.
        '''
        assert names or contexts, 'At least a name or context is required'
        if __debug__:
            for name in names: assert isinstance(name, str), 'Invalid context name %s' % name
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        self._usingContexts.update(contexts)
        self._usingNames.update(contexts)
        self._usingNames.update(names)
        
        return self
        
    def process(self, sources, resolvers, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(sources, dict), 'Invalid sources %s' % sources
        assert isinstance(extensions, dict), 'Invalid extensions %s' % extensions
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Routing \'%s\'' % self.name())
        
        try:
            rresolvers, rextensions = {}, {}
            calls = self._processAssembly(sources, rresolvers, rextensions, report)
            
        except: raise AssemblyError('Cannot process Routing for \'%s\'' % self.name())
            
        try:
            merge(resolvers, copyAttributes(rresolvers, attributesFor(sources)))
            solve(rresolvers, sources)
            if checkIf(rresolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Routing for \'%s\' has unavailable attributes:%s' % 
                                    (self.name(), reportFor(rresolvers, LIST_UNAVAILABLE)))
            solve(rresolvers, rextensions)
            merge(extensions, rresolvers)
            
            uresolvers = extractContexts(rresolvers, self._usingNames)
            uresolvers = solve(uresolvers, self._usingContexts)
            if checkIf(uresolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Routing for \'%s\' has unavailable attributes:%s' % 
                                    (self.name(), reportFor(uresolvers, LIST_UNAVAILABLE)))
            solve(uresolvers, extractContexts(rextensions, self._usingNames))
            
            report.add(uresolvers)
            contexts = create(uresolvers)
            
            return Processing(calls, contexts)
        
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
                ('request', 'solicitation')
                    The assembly will receive as the 'request' context the 'solicitation' context.
                ('request', 'solicitation'), ('request': 'response')
                    The assembly will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation', 'request'), ('response': 'request')
                    The assembly will receive as the 'solicitation' and 'response' context the 'request' context.
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
        
        self._current = current
        self._contexts = contexts
    
    def process(self, sources, resolvers, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Using \'%s\'' % self.name())
        
        try:
            usources = restructureResolvers(resolvers, self._current)
            solve(usources, restructureResolvers(sources, self._current))
            merge(usources, self._contexts)
            uextensions, uresolvers = {}, {}
            calls = self._processAssembly(usources, uresolvers, uextensions, report)
            
        except: raise AssemblyError('Cannot process Using for \'%s\'' % self.name())
        
        try:
            solve(uresolvers, usources, False)
            if checkIf(uresolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Using for \'%s\' has unavailable attributes:%s' % 
                                    (self.name(), reportFor(uresolvers, LIST_UNAVAILABLE)))
            solve(uresolvers, uextensions)
            cextensions = restructureResolvers(uresolvers, self._current, True)
            cextensions = copyAttributes(cextensions, attributesFor(resolvers))
            merge(extensions, cextensions)
            
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
    
    def __init__(self, assembly):
        '''
        Construct the included branch.
        @see: WithAssembly.__init__
        '''
        super().__init__(assembly)
        
        self._names = set()
        self._usingContexts = {}
        self._usingNames = set()
    
    def only(self, *names):
        '''
        Register the context names required for including, if this method is not used the all contexts are used.
        
        @param names: arguments[string|tuple(string, string)]
            The contexts names to be included, or mappings to alter the included context names based on, attention the
            order in which the context mappings are provided is crucial, examples:
                ('request', 'solicitation')
                    The assembly will receive as the 'request' context the 'solicitation' context.
                ('request', 'solicitation'), ('request': 'response')
                    The assembly will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation', 'request'), ('response': 'request')
                    The assembly will receive as the 'solicitation' and 'response' context the 'request' context.
            The altering mappings are applied also on the using contexts.
        @return: self
            This branch for chaining purposes.
        '''
        assert names, 'At least a name or mapping is required'
        if __debug__:
            for name in names: assert isinstance(name, (str, tuple)), 'Invalid only name %s' % name
        self._names.update(names)
        
        return self
        
    def using(self, *names, **contexts):
        '''
        Register the context names required for using, basically the contexts that need to be present on the processing.
        
        @param names: arguments[string]
            The contexts names to be used rather then included.
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be used rather then included.
        @return: self
            This branch for chaining purposes.
        '''
        assert names or contexts, 'At least a name or context is required'
        if __debug__:
            for name in names: assert isinstance(name, str), 'Invalid context name %s' % name
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        self._usingContexts.update(contexts)
        self._usingNames.update(contexts)
        self._usingNames.update(names)
        
        return self
    
    def process(self, sources, resolvers, extensions, report):
        '''
        @see: IBrach.process
        '''
        assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
        assert isinstance(report, IReport), 'Invalid report %s' % report
        
        report = report.open('Included \'%s\'' % self.name())
        
        try:
            if self._names: sources = restructureResolvers(sources, self._names)
            iresolvers, iextensions = {}, {}
            calls = self._processAssembly(sources, iresolvers, iextensions, report)
            if self._names:
                iresolvers = restructureResolvers(iresolvers, self._names, True)
                iextensions = restructureResolvers(iextensions, self._names, True)
            
            uresolvers = extractContexts(iresolvers, self._usingNames)
            uresolvers = solve(uresolvers, self._usingContexts)
            if checkIf(uresolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Included for \'%s\' has unavailable attributes:%s' % 
                                    (self.name(), reportFor(uresolvers, LIST_UNAVAILABLE)))
            solve(uresolvers, extractContexts(iextensions, self._usingNames))
            
            report.add(uresolvers)
            contexts = create(uresolvers)
            
            solve(resolvers, iresolvers)
            solve(extensions, iextensions)
            return Processing(calls, contexts)
        
        except: raise AssemblyError('Cannot process Included for \'%s\'' % self.name())
