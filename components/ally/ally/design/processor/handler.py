'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the handlers support.
'''

from .assembly import Container
from .branch import Routing
from .context import Context
from .execution import Chain
from .processor import Composite, Contextual, Brancher, Renamer, Processor
from .resolvers import resolverFor, solve, resolversFor
from .spec import ContextMetaClass, IProcessor, ProcessorError, IResolver
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
        super().__init__(push(Contextual(self.process), **contexts))

    @abc.abstractclassmethod
    def process(self, chain, **keyargs):
        '''
        The contextual process function used by the handler.
        
        @param chain: Chain
            The processing chain.
        '''
        
class HandlerComposite(Handler):
    '''
    A handler that contains a processor derived on the contextual 'process' function and allows other processors to be
    added.
    '''

    def __init__(self, *processors, **contexts):
        '''
        Construct the handler with the processor automatically created from the 'process' function.
        
        @param processors: arguments[IProcessor]
            Additional processors to be incorporated into the handler.
        @param contexts: key arguments
            Additional context that are not used in the contextual function but they are required in assembly.
        '''
        super().__init__(Composite(push(Contextual(self.process), **contexts), *processors))

    @abc.abstractclassmethod
    def process(self, chain, **keyargs):
        '''
        The contextual process function used by the handler.
        
        @param chain: Chain
            The processing chain.
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
        super().__init__(push(Brancher(self.process, *branches), **contexts))

    @abc.abstractclassmethod
    def process(self, chain, *processings, **keyargs):
        '''
        The contextual process function used by the handler.
        
        @param chain: Chain
            The processing chain.
        @param processings: arguments[Processing]
            The processings to use for branching, in the order the initial branches setups have been provided.
        '''

# --------------------------------------------------------------------

class RenamerHandler(Handler):
    '''
    Handler renamer that wraps a container or a processor with the purpose of renaming contexts.
    '''
    
    def __init__(self, target, *mapping):
        '''
        Construct the handler renamer.
        
        @param target: Container|Processor
            Restructures the provided target.
        @param mapping: arguments[tuple(string, string)]
            The mappings that the renamer needs to make, also the context to be passed along without renaming need to
            be provided as simple names, attention the order in which the context mappings are provided is crucial, examples:
                ('request', 'solicitation')
                    The wrapped processor will receive as the 'request' context the 'solicitation' context.
                ('request', 'solicitation'), ('request', 'response')
                    The wrapped processor will receive as the 'request' context the 'solicitation' and 'response' context.
                ('solicitation', 'request'), ('response', 'request')
                    The wrapped processor will receive as the 'solicitation' and 'response' context the 'request' context.
        '''
        if isinstance(target, Container):
            assert isinstance(target, Container)
            assert len(target.processors) == 1, 'Container %s, is required to have only one processor' % target
            processor = target.processors[0]
        assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
        super().__init__(Renamer(processor, *mapping))

class RoutingHandler(HandlerBranching):
    '''
    Implementation for a handler that provides routing to a designated container.
    '''
    
    def __init__(self, target):
        super().__init__(Routing(target))
            
    def process(self, chain, processing, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the routing.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        chain.route(processing)
            
# --------------------------------------------------------------------

def push(container, **contexts):
    '''
    Pushes into the processor the additional provided contexts.
    
    @param container: Container|Contextual
        The processor to push the context in.
    @param contexts: key arguments of ContextMetaClass|IResolver}
        The context classes to push.
    @return: Container|Contextual
        The same container.
    '''
    if isinstance(container, Contextual): processor = container
    elif isinstance(container, Container):
        assert isinstance(container, Container)
        assert len(container.processors) == 1, 'Container %s, is required to have only one processor' % container
        processor = container.processors[0]
    assert isinstance(processor, Contextual), 'Invalid processor %s' % processor
    for name, context in contexts.items():
        assert isinstance(name, str), 'Invalid name %s' % name
        if isinstance(context, tuple):
            assert context, 'At least one context class is required'
            multiple = context
            context = None
            for clazz in multiple:
                assert clazz is not Context, 'Context class is an invalid class'
                assert isinstance(clazz, (ContextMetaClass, IResolver)), 'Invalid context class %s' % context
                if context is None:
                    if isinstance(clazz, IResolver): context = clazz
                    else: context = resolverFor(clazz)
                else: context = context.solve(clazz if isinstance(clazz, IResolver) else resolverFor(clazz))
        
        assert isinstance(context, (ContextMetaClass, IResolver)), 'Invalid context class %s' % context
        if name in processor.contexts and processor.contexts[name] is not Context:
            raise ProcessorError('There is already a context for name \'%s\ in:%s' % (name, locationStack(processor.function)))
        processor.contexts[name] = context
    return container

def export(container, **contexts):
    '''
    Used in order to indicate the exported contexts.
    
    @param handler: Container|Processor
        The handler or processor to publish the export to.
    @param contexts: dictionary{string: ContextMetaClass|IResolver}
        The context classes or resolvers to export.
    @return: Container|Contextual
        The same container.
    '''
    if isinstance(container, Processor): processor = container
    elif isinstance(container, Container):
        assert isinstance(container, Container)
        assert len(container.processors) == 1, 'Container %s, is required to have only one processor' % container
        processor = container.processors[0]
    assert isinstance(processor, Processor), 'Invalid processor %s' % processor
    solve(processor.exported, resolversFor(contexts))
    return container
