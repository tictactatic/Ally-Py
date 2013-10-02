'''
Created on May 30, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembly contexts management and injection.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly, log
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context, create
from ally.design.processor.execution import Processing, Chain, Abort, FILL_ALL
from ally.design.processor.handler import Handler
from ally.design.processor.report import ReportUnused
from ally.design.processor.resolvers import resolversFor, solve, checkIf, \
    reportFor, merge
from ally.design.processor.spec import IProcessor, LIST_UNAVAILABLE, \
    AssemblyError, IResolver, LIST_UNUSED, LIST_CLASSES
from ally.support.util import FlagSet
from ally.support.util_spec import IDo
from collections import Iterable

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    services = defines(Iterable, doc='''
    @rtype: Iterable(class)
    The classes that implement service APIs.
    ''')
    exclude = defines(set, doc='''
    @rtype: set(object)
    The invoker identifiers that dictate the invokers to be excluded from the process. This is set gets updated whenever
    there is a problem invoker and in the case the chain is no fully consumed another try is made with this exclusion set.
    ''')
    doSuggest = defines(IDo, doc='''
    @rtype: callable(*args)
    The suggest logger to be used for registration.
    ''')
   
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    id = requires(str)

# --------------------------------------------------------------------

@injected
class InjectorAssemblyHandler(Handler, IProcessor):
    '''
    Implementation for a processor that manages the assemblers assembly contexts.
    '''
    
    assembly = Assembly
    # The assembly with the assemblers processors.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(self)
        
        self.done = False
        
        self.resolvers = {}
        self.extensions = {}
        self.wrappers = {}
        self.calls = []
        self.report = ReportUnused()
        
        sources = resolversFor(dict(register=Register, Invoker=Invoker))
        for processor in self.assembly.processors:
            assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
            processor.register(sources, self.resolvers, self.extensions, self.calls, self.report)
        for processor in self.processors:
            processor.finalized(sources, self.resolvers, self.extensions, self.report)
        
        solve(self.resolvers, sources)
        
        for name, resolver in self.resolvers.items(): self.wrappers[name] = ResolverWrapper(resolver)

    def process(self, chain, **keyargs):
        '''
        Injects in the chain the assembly contexts.
        '''
        assert self.done, 'Cannot process because no service registering has been performed'
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        chain.process(self.assembled)
        
    # ----------------------------------------------------------------
    
    def register(self, sources, resolvers, extensions, calls, report):
        '''
        @see: IProcessor.register
        '''
        assert not self.done, 'Cannot register anymore the service registering has been performed already'
        merge(resolvers, self.wrappers)
        calls.append(self.process)
        
    def finalized(self, sources, resolvers, extensions, report):
        '''
        @see: IProcessor.finalized
        '''
        assert not self.done, 'Cannot register anymore the service registering has been performed already'
        assert isinstance(sources, dict), 'Invalid sources %s' % sources
        assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
        assert isinstance(extensions, dict), 'Invalid extensions %s' % extensions
        
        solve(self.resolvers, self.filter(sources))
        solve(self.resolvers, self.filter(resolvers))
        solve(self.resolvers, self.filter(extensions))
        
    def filter(self, resolvers):
        '''
        Filters the provided resolvers.
        '''
        assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
        extracted = {name: resolver.wrapped if isinstance(resolver, ResolverWrapper) else resolver
                     for name, resolver in resolvers.items() if name in self.resolvers}
        for name in extracted: resolvers.pop(name, None)
        return extracted

    # ----------------------------------------------------------------
    
    def registerServices(self, services):
        '''
        Register the services.
        '''
        if not self.done:
            self.done = True
        
            if checkIf(self.resolvers, LIST_UNAVAILABLE):
                raise AssemblyError('Injected assembly \'%s\' has unavailable attributes:\n%s' % 
                                    (self.assembly.name, reportFor(self.resolvers, LIST_UNAVAILABLE)))
            solve(self.resolvers, self.extensions)

            self.processing = Processing(self.calls, create(self.resolvers))
            reportAss = self.report.open('injected assembly \'%s\'' % self.assembly.name)
            reportAss.add(self.resolvers)
            
            message = self.report.report()
            if message: log.info('\n%s\n' % message)
            else: log.info('Nothing to report for \'%s\', everything fits nicely', self.assembly.name)
            
            # We clean up the data that is not needed anymore
            del self.resolvers
            del self.extensions
            del self.wrappers
            del self.calls
            del self.report
        
        exclude, aborted = set(), 0
        while True:
            suggestions = []
            register = self.processing.ctx.register(services=iter(services),
                                                  exclude=exclude, doSuggest=lambda *args: suggestions.append(args))
            try:
                self.assembled = self.processing.execute(FILL_ALL, register=register)
                break
            except Abort as e:
                assert isinstance(e, Abort)
                found = set()
                for reason in e.reasons:
                    if isinstance(reason, Invoker):
                        assert isinstance(reason, Invoker)
                        assert isinstance(reason.id, str), 'Invalid invoker id %s' % reason.id
                        if reason.id in exclude:
                            log.error('Already excluded %s', reason)
                            return
                        found.add(reason.id)
                if not found:
                    log.error('Could not locate any invoker reason in %s', e.reasons)
                    return
                exclude.update(found)
                aborted += 1
                
        log.info('Finalized assemblers after %i aborts' % aborted)
        if suggestions:
            log.warn('Available suggestions:\n%s', '\n'.join(suggest[0] % suggest[1:] for suggest in suggestions))
            
# --------------------------------------------------------------------

class ResolverWrapper(IResolver):
    '''
    Implementation for a @see: IResolver that just prevents the detection of unused attributes and also keeps track of the
    actually used ones.
    '''
    __slots__ = ('wrapped',)
    
    def __init__(self, wrapped):
        '''
        Constructs the resolver wrapper.
        
        @param wrapped: IResolver
            The wrapped resolver.
        '''
        assert isinstance(wrapped, IResolver), 'Invalid wrapped resolver %s' % wrapped
        self.wrapped = wrapped
        
    def copy(self, names=None):
        '''
        @see: IResolver.copy
        '''
        return ResolverWrapper(self.wrapped.copy(names))
         
    def merge(self, other, isFirst=True):
        '''
        @see: IResolver.merge
        '''
        return ResolverWrapper(self.wrapped.merge(other, isFirst))
        
    def solve(self, other):
        '''
        @see: IResolver.solve
        '''
        return ResolverWrapper(self.wrapped.solve(other))
        
    def list(self, *flags):
        '''
        @see: IResolver.list
        '''
        flags = FlagSet(flags)
        if not flags.checkOnce(LIST_UNUSED): return self.wrapped.list(*flags)
        if LIST_UNAVAILABLE in flags: return self.wrapped.list(*flags)
        flags.discard(LIST_CLASSES)
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return {}
        
    def create(self, *flags):
        '''
        @see: IResolver.create
        '''
        return self.wrapped.create(*flags)
