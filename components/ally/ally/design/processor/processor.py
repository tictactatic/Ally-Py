'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing processors.
'''

from .assembly import Container
from .execution import Chain, Processing
from .merging import mergeAttributes, iterateAttributes, solveAttributes, \
    createObject, extract, validateForObject
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

    def register(self, contexts, attributes, calls):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        mergeAttributes(attributes, iterateAttributes(self.contexts), processor=self)
        calls.append(self.call)
        
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
        
    def register(self, contexts, attributes, calls):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        try: mergeAttributes(attributes, iterateAttributes(self.contexts), processor=self)
        except AttrError: raise AssemblyError('Cannot merge contexts at:%s' % locationStack(self.function))
        calls.append(self.call)
        
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
    def process(self, processor, contexts, attributes):
        '''
        Process the branch for the current contexts and attributes.
        
        @param processor: IProcessor
            The processor that is performing the branching.
        @param contexts: dictionary{string, ContextMetaClass}
            The contexts that need to be solved.
        @param attributes: dictionary{tuple(string, string), IAttribute}
            The attributes that are so far generated by processors, whenever registration is made this dictionary needs
            to be merged with the processor contexts attributes. The key is formed as a tuple having on the first position
            the context name and in the second position the attribute name.
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
    
    def register(self, contexts, attributes, calls):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        self.processings = []
        for branch in self.branches:
            assert isinstance(branch, IBranch), 'Invalid branch %s' % branch
            try: processing = branch.process(self, contexts, attributes)
            except AttrError: raise AssemblyError('Cannot create processing at:%s' % locationStack(self.function))
            assert isinstance(processing, Processing), 'Invalid processing %s' % processing
            self.processings.append(branch.process(self, contexts, attributes))
            
        calls.append(self.call)
        
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

class Included(IBranch):
    '''
    Branch for included processors containers. By included is understood that the processors will be executed using the
    main context objects, so basically is like having included also the processors in the main chain but still have control
    over when and how they are executed.
    '''
    __slots__ = ('container',)
    
    def __init__(self, container):
        '''
        Construct the included branch.
        
        @param container: Container
            The processors container to be included.
        '''
        assert isinstance(container, Container), 'Invalid container %s' % container
        self.container = container
        
    def process(self, processor, contexts, attributes):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        
        attributesContainer, calls = {}, []
        for proc in self.container.processors:
            assert isinstance(proc, IProcessor), 'Invalid processor %s' % proc
            proc.register(contexts, attributesContainer, calls)
            
        solveAttributes(attributesContainer, iterateAttributes(processor.contexts), processor=processor)
        mergeAttributes(attributes, attributesContainer, processor=processor)
        
        return Processing(calls)

class Routing(IBranch):
    '''
    Branch for routed processors containers. By routing is understood that the processors will be executed separately
    from the main chain and they need to solve the main contexts. 
    '''
    __slots__ = ('container', 'merged')
    
    def __init__(self, container, merged=True):
        '''
        Construct the routing branch.
        
        @param container: Container
            The processors container that provides routing.
        @param merged: boolean
            Flag indicating that the routing should be merged with the main context, thus allowing the routing processor
            to use the same objects.
            Attention if this is true then no processing context will be available.
        '''
        assert isinstance(container, Container), 'Invalid container %s' % container
        assert isinstance(merged, bool), 'Invalid merged flag %s' % merged
        self.container = container
        self.merged = merged
        
    def process(self, processor, contexts, attributes):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        
        attributesContainer, calls = {}, []
        for proc in self.container.processors:
            assert isinstance(proc, IProcessor), 'Invalid processor %s' % proc
            proc.register(contexts, attributesContainer, calls)
        
        solveAttributes(attributesContainer, iterateAttributes(processor.contexts), processor=processor)
        
        if self.merged:
            attributesContainer = solveAttributes(attributes, attributesContainer)
            solveAttributes(attributesContainer, iterateAttributes(contexts), processor=processor)
            validateForObject(attributesContainer)
            
            return Processing(calls)
        
        mergeAttributes(attributes, iterateAttributes(processor.contexts), processor=processor)
        attributesContainer = mergeAttributes(dict(attributes), attributesContainer, processor=processor)
        solveAttributes(attributesContainer, iterateAttributes(contexts), processor=processor)
        
        return Processing(calls, createObject(attributesContainer))
        
class Using(IBranch):
    '''
    Branch for using processors containers. By using is understood that the processors will be executed separately
    from the main chain and they need to solve the provided contexts. 
    '''
    __slots__ = ('container', 'merged', 'contexts')
    
    def __init__(self, container, merged=True, **contexts):
        '''
        Construct the using branch.
        
        @param container: Container
            The processors container to use.
        @param merged: boolean
            Flag indicating that beside the provided context also ongoing context will be provided.
        @param contexts: key arguments{string, ContextMetaClass}
            The contexts to be solved by the used container.
        '''
        assert isinstance(container, Container), 'Invalid container %s' % container
        assert isinstance(merged, bool), 'Invalid merged flag %s' % merged
        if __debug__:
            for name, clazz in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        self.container = container
        self.merged = merged
        self.contexts = contexts
        
    def process(self, processor, contexts, attributes):
        '''
        @see: IBrach.process
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        
        calls = []
        if self.merged:
            attributesContainer = dict(attributes)
        else:
            attributesContainer = {}

        for proc in self.container.processors:
            assert isinstance(proc, IProcessor), 'Invalid processor %s' % proc
            proc.register(contexts, attributesContainer, calls)
        
        solveAttributes(attributesContainer, iterateAttributes(self.contexts), processor=processor)
        
        if self.merged:
            required = {}
            for name in self.contexts: required.update(extract(attributesContainer, name))
            mergeAttributes(attributes, ((key, attr) for key, attr in attributesContainer.items() if key not in required),
                            processor=processor)
        else:
            mergeAttributes(attributes, iterateAttributes(processor.contexts), processor=processor)
            required = attributesContainer
            
        return Processing(calls, createObject(required))
