'''
Created on Mar 18, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the accessible paths for a model.
'''

from ally.container.ioc import injected
from ally.core.http.spec.server import IEncoderPathInvoker
from ally.core.http.spec.transform.index import NAME_BLOCK_REST, \
    ACTION_REFERENCE
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import OrderedDict
from ally.api.operator.type import TypeModel
import logging
from ally.support.util_sys import locationStack

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokersAccessible = requires(OrderedDict)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    target = requires(TypeModel)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Required
    pathValues = requires(dict)
    encoderPathInvoker = requires(IEncoderPathInvoker)

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the accessible paths.
    ''')
    
# --------------------------------------------------------------------

@injected
class AccessiblePathEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the accessible paths encoding.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(Support=Support)
        
    def process(self, chain, node:Node, invoker:Invoker, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the accesible path encoder.
        '''
        assert isinstance(node, Node), 'Invalid node %s' % node
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not node.invokersAccessible: return  # No accessible paths
        if not invoker.target: return  # No target available
        if create.encoder is not None: return  # There is already an encoder, nothing to do.
        assert isinstance(invoker.target, TypeModel), 'Invalid target %s' % invoker.target
        
        nameTarget = invoker.target.container.name
        accessible = OrderedDict(('%s%s' % (nameTarget, name), invoker) for name, invoker in node.invokersAccessible.items())
        create.encoder = EncoderAccessiblePath(self.nameRef, accessible)
        
        for name in invoker.target.container.properties:
            if name.startswith(nameTarget):
                log.warn('Illegal property name \'%s\', is not allowed to start with the model name, at:%s',
                         name, locationStack(invoker.target.clazz))

# --------------------------------------------------------------------

class EncoderAccessiblePath(IEncoder):
    '''
    Implementation for a @see: IEncoder for model paths.
    '''
    
    def __init__(self, nameRef, accessible):
        '''
        Construct the model paths encoder.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(accessible, OrderedDict) and accessible, 'Invalid accessible invokers %s' % accessible
        
        self.nameRef = nameRef
        self.accessible = accessible
    
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.encoderPathInvoker, IEncoderPathInvoker), \
        'Invalid encoder path %s' % support.encoderPathInvoker
        
        indexes = dict(indexBlock=NAME_BLOCK_REST, indexAttributesCapture={self.nameRef: ACTION_REFERENCE})
        for name, invoker in self.accessible.items():
            path = support.encoderPathInvoker.encode(invoker, support.pathValues)
            render.beginObject(name, attributes={self.nameRef: path}, **indexes).end()
