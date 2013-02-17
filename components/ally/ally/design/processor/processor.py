'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing processors.
'''

from .assembly import Assembly
from .execution import Chain, Processing
from .merging import Merger
from .spec import AttrError, AssemblyError, IProcessor, ContextMetaClass, \
    ProcessorError
from ally.support.util_sys import locationStack
from collections import Iterable
from inspect import ismethod, isfunction, getfullargspec
from itertools import chain
import abc

# --------------------------------------------------------------------

class Processor(IProcessor):
    '''
    Implementation for @see: IProcessor that takes as the call a function and uses the annotations on the function arguments 
    to extract the contexts.
    '''
    __slots__ = ('contexts', 'call')
    
    def __init__(self, contexts, call):
        '''
        Construct the processor for the provided context having the provided call.
        
        @param contexts: dictionary{string, ContextMetaClass}
            The contexts to be associated with the processor.
        @param call: callable
            The call of the processor.
        '''
        assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
        assert callable(call), 'Invalid call %s' % call
        if __debug__:
            for key, clazz in contexts.items():
                assert isinstance(key, str), 'Invalid context name %s' % key
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s for %s' % (clazz, key)

        self.contexts = contexts
        self.call = call

    def register(self, merger):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        merger.merge(self.contexts)
        merger.addCall(self.call)
        
    # ----------------------------------------------------------------

    def __eq__(self, other):
        if not isinstance(other, self.__class__): return False
        return self.contexts == other.contexts and self.call == other.call

class Contextual(Processor):
    '''
    Implementation for @see: IProcessor that takes as the call a function and uses the annotations on the function arguments 
    to extract the contexts.
    '''
    __slots__ = ('proceed', 'function')

    def __init__(self, function, proceed=False):
        '''
        Constructs a processor based on a function.
        @see: Processor.__init__
        
        @param function: function|method
            The function of the processor with the arguments annotated.
        @param proceed: boolean
            Flag indicating that the processor should auto proceed for the executed chain.
            Attention if this flag is provided then the function should not have a 'chain' argument.
        '''
        assert isinstance(proceed, bool), 'Invalid proceed flag %s' % proceed
        assert isfunction(function) or ismethod(function), 'Invalid function %s' % function
        
        self.proceed = proceed
        self.function = function
        
        fnArgs = getfullargspec(function)
        arguments, annotations = self.processArguments(fnArgs.args, fnArgs.annotations)
        
        assert isinstance(arguments, Iterable), 'Invalid arguments %s' % arguments
        assert isinstance(annotations, dict), 'Invalid annotations %s' % annotations
        contexts = {}
        for name in arguments:
            assert isinstance(name, str), 'Invalid argument name %s' % name
            clazz = annotations.get(name)
            if clazz is None: continue
            if not isinstance(clazz, ContextMetaClass):
                raise ProcessorError('Not a context class %s for argument %s, at:%s' % 
                                     (clazz, name, locationStack(self.function)))
            contexts[name] = clazz
        if not contexts: raise ProcessorError('Cannot have a function with no context, at:%s' % 
                                              locationStack(self.function))
        
        super().__init__(contexts, self.processCall(function))
        
    def register(self, merger):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        
        try: merger.merge(self.contexts)
        except AttrError: raise AssemblyError('Cannot merge contexts at:%s' % locationStack(self.function))
        merger.addCall(self.call)
        
    # ----------------------------------------------------------------
     
    def processArguments(self, arguments, annotations):
        '''
        Process the context arguments as seen fit.
        
        @param arguments: list[string]|tuple(string)
            The arguments to process.
        @param annotations: dictionary{string, object}
            The annotations to process.
        @return: tuple(list[string], dictionary{string, object})
            A tuple containing the list of processed arguments names and second value the dictionary containing the 
            annotation for arguments.
        '''
        assert isinstance(arguments, (list, tuple)), 'Invalid arguments %s' % arguments
        assert isinstance(annotations, dict), 'Invalid annotations %s' % annotations
        if self.proceed:
            if len(arguments) > 1 and 'self' == arguments[0]: return arguments[1:], annotations
            raise ProcessorError('Required function of form \'def processor(self, contex:Context ...)\' for:%s' % 
                                 locationStack(self.function))

        if len(arguments) > 2 and 'self' == arguments[0]: return arguments[2:], annotations
        raise ProcessorError('Required function of form \'def processor(self, chain, contex:Context ...)\' for:%s' % 
                             locationStack(self.function))
    
    def processCall(self, call):
        '''
        Process the call of the process if is the case.
        
        @param call: callable
            The call to wrap.
        @return: callable
            The wrapped call.
        '''
        if self.proceed:
            def wrapper(chain, **keyargs):
                assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
                call(**keyargs)
                chain.proceed()
            return wrapper
        return call
    
    # ----------------------------------------------------------------
    
    def __str__(self):
        ctxs = '\n'.join(('%s=%s' % item for item in self.contexts.items()))
        if ismethod(self.function):
            return '%s with:\n%s\n, defined at:%s\n, in instance %s' % \
                (self.__class__.__name__, ctxs, locationStack(self.function), self.function.__self__)
        return '%s with:\n%s\n, defined at:%s' % (self.__class__.__name__, ctxs, locationStack(self.function))

# --------------------------------------------------------------------

class IBranch(metaclass=abc.ABCMeta):
    '''
    Specification for a branch handler.
    '''
    __slots__ = ()
    
    @abc.abstractmethod
    def process(self, processor, merger):
        '''
        Process the branch for the current contexts and attributes.
        
        @param processor: IProcessor
            The processor that is performing the branching.
        @param merger: Merger
            The merger that needs to be solved.
        @return: IProcessing
            The branch processing.
        ''' 

class Brancher(Contextual):
    '''
    Implementation for @see: IProcessor that provides branching of other processors containers.
    '''
    __slots__ = ('branches', 'processings')
    
    def __init__(self, function, *branches, proceed=False):
        '''
        Construct the branching processor.
        @see: Contextual.__init__
        
        @param branches: arguments[IBranch]
            The branches to use in branching.
        '''
        assert branches, 'At least one branch is required'
        if __debug__:
            for branch in branches: assert isinstance(branch, IBranch), 'Invalid branch %s' % branch
        self.branches = branches
        super().__init__(function, proceed)
    
    def register(self, merger):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        
        self.processings = []
        for branch in self.branches:
            assert isinstance(branch, IBranch), 'Invalid branch %s' % branch
            try: processing = branch.process(self, merger)
            except AttrError: raise AssemblyError('Cannot create processing at:%s' % locationStack(self.function))
            assert isinstance(processing, Processing), 'Invalid processing %s' % processing
            self.processings.append(processing)
        merger.addCall(self.call)
        
    # ----------------------------------------------------------------
        
    def processArguments(self, arguments, annotations):
        '''
        @see: Contextual.processArguments
        '''
        arguments, annotations = super().processArguments(arguments, annotations)
        
        n = len(self.branches)
        if len(arguments) > n: return arguments[n:], annotations
        raise ProcessorError('Required function of form \'def processor(self, [chain], '
                             'processing, ..., contex:Context ...)\' for:%s' % locationStack(self.function))
    
    def processCall(self, call):
        '''
        @see: Contextual.processCall
        '''
        def wrapper(*args, **keyargs):
            call(*chain(args, self.processings), **keyargs)
        return super().processCall(wrapper)

# --------------------------------------------------------------------

class Routing(IBranch, IProcessor):
    '''
    Branch for routed processors containers. By routing is understood that the processors will be executed separately
    from the main chain and they need to solve the main contexts. 
    '''
    __slots__ = ('assembly', 'merged')
    
    def __init__(self, assembly, merged=True):
        '''
        Construct the routing branch.
        
        @param assembly: Assembly
            The processors assembly that provides routing.
        @param merged: boolean
            Flag indicating that the routing should be merged with the main context, thus allowing the routing processor
            to use the same objects.
            Attention if this is true then no processing context will be available.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        assert isinstance(merged, bool), 'Invalid merged flag %s' % merged
        self.assembly = assembly
        self.merged = merged
        
    def process(self, processor, merger):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        
        merger.merge(processor.contexts)
        
        bmerger = merger.branch('Routing %s' % self.assembly.name)
        assert isinstance(bmerger, Merger)
        bmerger.processNow(self.assembly.processors)
        bmerger.solve(processor.contexts)
        bmerger.mergeWithParent()
        
        if self.merged:
            bmerger.addOnNext(self)
            return Processing(bmerger.calls())
        
        bmerger.resolve()
        bmerger.processAllNext()
        return Processing(bmerger.calls(), bmerger.createContexts())
        
    def register(self, merger):
        '''
        @see: IProcessor.register
        
        Register the merged attributes.
        '''
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        merger.solveOnParent()
  
class Using(IBranch):
    '''
    Branch for using processors containers. By using is understood that the processors will be executed separately
    from the main chain and they need to solve the provided contexts. 
    '''
    __slots__ = ('assembly', 'contexts')

    def __init__(self, assembly, **contexts):
        '''
        Construct the using branch.
        
        @param assembly: Assembly
            The processors assembly to use.
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be solved by the used container.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if __debug__:
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        self.assembly = assembly
        self.contexts = contexts
        
    def process(self, processor, merger):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        
        merger.merge(processor.contexts)
        
        nmerger = merger.branchNew('Using %s' % self.assembly.name, self.contexts)
        assert isinstance(nmerger, Merger)
        nmerger.processNow(self.assembly.processors)
        nmerger.resolve()
        nmerger.processAllNext()
        return Processing(nmerger.calls(), nmerger.createContexts())

class Included(IBranch):
    '''
    Branch for included processors containers. By included is understood that the processors will be executed using the
    main context objects, so basically is like having included also the processors in the main chain but still have control
    over when and how they are executed.
    '''
    __slots__ = ('assembly', 'contextsUsing')
    
    def __init__(self, assembly):
        '''
        Construct the included branch.
        
        @param assembly: Container
            The processors assembly to be included.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        self.assembly = assembly
        self.contextsUsing = {}
        
    def process(self, processor, merger):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        assert isinstance(merger, Merger), 'Invalid merger %s' % merger
        
        bmerger = merger.branch('Included %s' % self.assembly.name)
        assert isinstance(bmerger, Merger)
        bmerger.processNow(self.assembly.processors)
        
        if self.contextsUsing:
            umerger = bmerger.branchExtract('Using from Included \'%s\'' % self.assembly.name, self.contextsUsing)
            assert isinstance(umerger, Merger)
            umerger.resolve()
            umerger.processAllNext()
            contexts = umerger.createContexts()
        
        bmerger.solve(processor.contexts)
        bmerger.mergeOnParent()
        
        processing = Processing(bmerger.calls())
        assert isinstance(processing, Processing)
        if self.contextsUsing: processing.update(**contexts)
        
        return processing
    
    # ----------------------------------------------------------------
    
    def using(self, **contexts):
        '''
        Declare the contexts that will not be included but will be used. This means that this context will be on processing
        contexts and have instances created for.
        
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be used rather then included.
        @return: self
            This instance for chaining purposes.
        '''
        if __debug__:
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        self.contextsUsing.update(**contexts)
        return self
