'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the handlers support.
'''

from .assembly import Container
from .processor import Contextual, Brancher, ProcessorRenamer
from .spec import ContextMetaClass, IProcessor, ProcessorError
from ally.support.util_sys import locationStack
import abc

# --------------------------------------------------------------------

class Handler(Container):
    '''
    Handler base that provides a container for a processor.
    '''

    def __init__(self, processor):
        '''
        Construct the handler.
        
        @param processor: IProcessor
            The processor for the container.
        '''
        super().__init__(processor)

class HandlerProcessor(Handler):
    '''
    A handler that contains a processor derived on the contextual 'process' function.
    '''

    def __init__(self, **contexts):
        '''
        Construct the handler with the processor automatically created from the 'process' function.
        
        @param contexts: key arguments
            Additional context that are not used in the contextual function but they are required in assembly.
        '''
        super().__init__(push(Contextual(self.process, proceed=False), contexts))

    @abc.abstractclassmethod
    def process(self, chain, **keyargs):
        '''
        The contextual process function used by the handler.
        
        @param chain: Chain
            The processing chain.
        '''

class HandlerProcessorProceed(Handler):
    '''
    A handler that contains a processor derived on the contextual 'process' function and automatically proceeds the chain.
    '''

    def __init__(self, **contexts):
        '''
        Construct the handler with the processor automatically created from the 'process' function.
        
        @param contexts: key arguments
            Additional context that are not used in the contextual function but they are required in assembly.
        '''
        super().__init__(push(Contextual(self.process, proceed=True), contexts))

    @abc.abstractclassmethod
    def process(self, **keyargs):
        '''
        The contextual process function used by the handler, this process will not require a chain and will always
        proceed with the execution.
        '''
        
# --------------------------------------------------------------------

class HandlerBranching(Handler):
    '''
    A handler that contains a processor derived on the contextual 'process' function that also provides branching for other
    processors containers based on the setup provided at construction.
    '''

    def __init__(self, *branches, **contexts):
        '''
        Construct the handler with the processor automatically created from the 'process' function and the including or 
        branching based on the provided processors containers.
        
        @param branches: arguments[IBranch]
            The branches used in branching, attention the order provided for setups will be reflected in the provided 
            processing order.
        @param contexts: key arguments
            Additional context that are not used in the contextual function but they are required in assembly.
        '''
        super().__init__(push(Brancher(self.process, *branches, proceed=False), contexts))

    @abc.abstractclassmethod
    def process(self, chain, *processings, **keyargs):
        '''
        The contextual process function used by the handler.
        
        @param chain: Chain
            The processing chain.
        @param processings: arguments[Processing]
            The processings to use for branching, in the order the initial branches setups have been provided.
        '''
        
class HandlerBranchingProceed(Handler):
    '''
    A handler that contains a processor derived on the contextual 'process' function that also provides branching
    and automatically proceeds the chain.
    '''
    
    def __init__(self, *branches, **contexts):
        '''
        Construct the handler with the processor automatically created from the 'process' function and the including or 
        branching based on the provided processors containers.
        
        @param branches: arguments[IBranch]
            The branches used in branching, attention the order provided for setups will be reflected in the provided 
            processing order.
        @param contexts: key arguments
            Additional context that are not used in the contextual function but they are required in assembly.
        '''
        super().__init__(push(Brancher(self.process, *branches, proceed=True), contexts))


    @abc.abstractclassmethod
    def process(self, *processings, **keyargs):
        '''
        The contextual process function used by the handler, this process will not require a chain and will always
        proceed with the execution.
        
        @param processings: arguments[Processing]
            The processings to use for branching, in the order the initial branches setups have been provided.
        '''
        
# --------------------------------------------------------------------

class HandlerRenamer(Handler):
    '''
    Handler renamer that wraps a container or a processor with the purpose of renaming contexts.
    '''
    
    def __init__(self, target, *mapping):
        '''
        Construct the handler renamer.
        
        @param target: Container|Processor
            Restructures the provided target.
        @param mapping: arguments[tuple(string, string)]
            The mappings that the renamer needs to make, attention the order in which the context mappings are provided
            is crucial, examples:
                ('request': 'solicitation')
                    The wrapped processor will receive as the 'request' context the 'solicitation' context.
                ('request': 'solicitation'), ('request': 'response')
                    The wrapped processor will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation': 'request'), ('response': 'request')
                    The wrapped processor will receive as the 'solicitation' and 'response' context the 'request' context.
        '''
        if isinstance(target, Container):
            assert isinstance(target, Container)
            assert len(target.processors) == 1, 'Container %s, is required to have only one processor' % target
            processor = target.processors[0]
        assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
        super().__init__(ProcessorRenamer(processor, *mapping))

# --------------------------------------------------------------------

def push(processor, contexts):
    '''
    Pushes into the processor the additional provided contexts.
    
    @param processor: Contextual
        The processor to push the context in.
    @param contexts: dictionary{string: COntextMetaClass}
        The context classes to push.
    @return: Contextual
        The same processor.
    '''
    assert isinstance(processor, Contextual), 'Invalid processor %s' % processor
    assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
    for name, context in contexts.items():
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(context, ContextMetaClass), 'Invalid context class %s' % context
        if name in processor.contexts:
            raise ProcessorError('There is already a context for name \'%s\ in:%s' % (name, locationStack(processor.function)))
        processor.contexts[name] = context
    return processor
