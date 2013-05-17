'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the callers created based on services.
'''

from ally.api.operator.container import Service, Call, Model
from ally.api.operator.type import TypeService, TypeModelProperty, TypeModel
from ally.api.type import typeFor, Input
from ally.core.impl.invoker import InvokerCall
from ally.core.spec.resources import Invoker, Node
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import Iterable
from ally.support.util_sys import locationStack
import itertools
from ally.core.impl.node import NodeProperty, NodePath

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    hintsModel = definesIf(dict, doc='''
    @rtype: dictionary{string: string}
    The available model hints, as a key the hint name and as a value the hint description.
    ''')
    # ---------------------------------------------------------------- Required
    root = requires(Node, doc='''
    @rtype: Node
    The root node to register to.
    ''')
    callers = requires(list)
    
class Caller(Context):
    '''
    The register caller context.
    '''
    # ---------------------------------------------------------------- Defined
    nodes = defines(list, doc='''
    @rtype: list[Node]
    The list of nodes where the invoker has to be placed.
    ''')
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)

# --------------------------------------------------------------------

class InputNodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the nodes where the registered invoker should be placed.
    '''
    
    hint = 'domain'
    # The hint name for the model domain.
    description = '(string) The domain where the model is registered'
    # The hint description.
    
    def __init__(self):
        assert isinstance(self.hint, str), 'Invalid hint name for model domain %s' % self.hint
        assert isinstance(self.description, str), 'Invalid hint description for model domain %s' % self.description
        super().__init__(Caller=Caller)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the nodes for the invoker.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(register.callers, list), 'Invalid callers %s' % register.callers
        assert isinstance(register.root, Node), 'Invalid root node %s' % register.root
        
        if Register.hintsModel in register:
            if register.hintsModel is None: register.hintsModel = {}
            register.hintsModel[self.hint] = self.description
        
        for caller in register.callers:
            assert isinstance(caller, Caller), 'Invalid caller %s' % caller
            assert isinstance(caller.invoker, Invoker), 'Invalid invoker %s' % caller.invoker
            assert isinstance(caller.model, TypeModel), 'Invalid target model %s' % caller.model
            assert isinstance(caller.model.container, Model), 'Invalid model %s' % caller.model.container
            
            node = register.root
            domain = caller.model.container.hints.get(self.hint)
            if domain:
                assert isinstance(domain, str) and domain, 'Invalid domain %s' % domain
                for name in domain.split('/'): node = self.obtainNodePath(node, name)
            
            optional = []
            for k, inp in enumerate(caller.invoker.inputs):
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                
                if isinstance(inp.type, TypeModelProperty):
                    if k < caller.invoker.mandatory:
                        if isinstance(node, NodeProperty):
                            assert isinstance(node, NodeProperty)
                            if inp not in node.inputs:
                                node = self.obtainNode(root, name)
        
                        if addModel: root = self.obtainNodeModel(root, model)
                        root = self.obtainNodeProperty(root, typ)
                    else: optional.append(inp)
                    
            if caller.nodes is None: caller.nodes = []
            for extra in itertools.chain(*(itertools.combinations(optional, k) for k in range(0, len(optional) + 1))):
                types = list(mandatory)
                types.extend(extra)
                
    def obtainNodePath(self, root, name, isGroup=False):
        '''
        Obtain the path node with name in the provided root Node.
        
        @param root: Node
            The root node to obtain the path node in.
        @param name: string
            The name for the path node.
        @param isGroup: boolean
            Flag indicating that the path node should be considered a group node (True) or an object node (False).
        @return: NodePath
            The path node.
        '''
        assert isinstance(root, Node), 'Invalid root node %s' % root
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(isGroup, bool), 'Invalid is group flag %s' % isGroup

        for child in root.children:
            if isinstance(child, NodePath) and child.name == name:
                if isGroup is not None: child.isGroup |= isGroup
                return child
        return NodePath(root, False if isGroup is None else isGroup, name)
    
    def obtainNodeProperty(self, root, inp):
        '''
        Obtain the property node in the provided root Node.
        
        @param root: Node
            The root node to obtain the path node in.
        @param inp: Input
            The input to find the node for.
        @return: NodeProperty
            The property node.
        '''
        assert isinstance(root, Node), 'Invalid root node %s' % root
        assert isinstance(inp, Input), 'Invalid input %s' % inp

        for child in root.children:
            if isinstance(child, NodeProperty) and child.isFor(inp):
                assert isinstance(child, NodeProperty)
                child.addInput(inp)
                return child
        return NodeProperty(root, inp)
                    
