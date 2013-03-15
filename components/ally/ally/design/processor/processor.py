'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing processors.
'''

from .branch import IBranch
from .context import Context
from .execution import Chain, Processing
from .manipulator import Mapping
from .repository import Repository
from .spec import AssemblyError, IProcessor, ContextMetaClass, ProcessorError, \
    IRepository
from ally.support.util_sys import locationStack
from collections import Iterable
from inspect import ismethod, isfunction, getfullargspec
from itertools import chain

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

    def register(self, sources, current, extensions, calls, report):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(current, IRepository), 'Invalid current repository %s' % current
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        current.merge(self.contexts)
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
            if clazz is None:
                raise ProcessorError('Context class required for argument %s, at:%s' % (name, locationStack(self.function)))
            if clazz is Context: continue
            if not isinstance(clazz, ContextMetaClass):
                raise ProcessorError('Not a context class %s for argument %s, at:%s' % 
                                     (clazz, name, locationStack(self.function)))
            contexts[name] = clazz
        if not contexts: raise ProcessorError('Cannot have a function with no context, at:%s' % 
                                              locationStack(self.function))
        
        super().__init__(contexts, self.processCall(function))
    
    def register(self, sources, current, extensions, calls, report):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(current, IRepository), 'Invalid current repository %s' % current
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        try: current.merge(self.contexts)
        except: raise AssemblyError('Cannot merge contexts at:%s' % locationStack(self.function))
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
            def wrapper(chain, *args, **keyargs):
                assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
                try: call(*args, **keyargs)
                except TypeError:
                    raise TypeError('Problems for arguments %s and key arguments %s for call at:%s' % 
                                    (args, keyargs, locationStack(call)))
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

class Brancher(Contextual):
    '''
    Implementation for @see: IProcessor that provides branching of other processors containers.
    '''
    __slots__ = ('branches',)
    
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
    
    def register(self, sources, current, extensions, calls, report):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        processings, processor = [], Repository(self.contexts)
        for branch in self.branches:
            assert isinstance(branch, IBranch), 'Invalid branch %s' % branch
            try: processing = branch.process(processor, sources, current, extensions, report)
            except: raise AssemblyError('Cannot create processing at:%s' % locationStack(self.function))
            assert isinstance(processing, Processing), 'Invalid processing %s' % processing
            processings.append(processing)
        
        def wrapper(*args, **keyargs): self.call(*chain(args, processings), **keyargs)
        calls.append(wrapper)
        
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

# --------------------------------------------------------------------

class ProcessorRenamer(IProcessor):
    '''
    Implementation for @see: IProcessor that renames the context names for the provided processor.
    '''
    __slots__ = ('processor', 'mapping')
    
    def __init__(self, processor, *mapping):
        '''
        Construct the processor that renames the context names for the provided processor.
        
        @param processor: Container|Processor
            Restructures the provided processor.
        @param mapping: arguments[tuple(string string)]
            The mappings that the renamer needs to make, attention the order in which the context mappings are provided
            is crucial, examples:
                ('request': 'solicitation')
                    The wrapped processor will receive as the 'request' context the 'solicitation' context.
                ('request': 'solicitation'), ('request': 'response')
                    The wrapped processor will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation': 'request'), ('response': 'request')
                    The wrapped processor will receive as the 'solicitation' and 'response' context the 'request' context.
        '''
        assert isinstance(processor, Processor), 'Invalid processor %s' % processor
        assert mapping, 'At least one mapping is required'
        
        self.mapping = Mapping()
        for first, second in mapping: self.mapping.map(first, second)
        self.processor = processor

    def register(self, sources, current, extensions, calls, report):
        '''
        @see: IProcessor.register
        '''
        assert isinstance(calls, list), 'Invalid calls %s' % calls
        
        wsources = self.mapping.structure(sources)
        wcurrent = self.mapping.structure(current)
        wextensions = self.mapping.structure(extensions)
        wcalls = []
        self.processor.register(wsources, wcurrent, wextensions, wcalls, report)
        
        self.mapping.restructure(current, wcurrent)
        self.mapping.restructure(extensions, wextensions)
        
        def wrapper(*args, **keyargs):
            for second, firsts in self.mapping.secondToFirst.items():
                try: value = keyargs.pop(second)
                except KeyError: continue
                for first in firsts: keyargs[first] = value
            
            for call in wcalls: call(*args, **keyargs)
        
        calls.append(wrapper)
