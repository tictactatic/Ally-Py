'''
Created on Aug 9, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the shadow invokers that just have duty to capture data in the path mostly for accessible invokers.
'''

from ally.api.operator.type import TypeProperty
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_GET
from ally.support.api.util_service import isCompatible
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    exclude = requires(set)
    doCopyInvoker = requires(IDo)
    doCopyElement = requires(IDo)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    shadowing = defines(Context, doc='''
    @rtype: Context
    The invoker that this shadow is made for.
    ''')
    shadowed = definesIf(Context, doc='''
    @rtype: Context
    The invoker that is shadowed.
    ''')
    # ---------------------------------------------------------------- Required
    id = requires(str)
    path = requires(list)
    methodHTTP = requires(str)
    isModel = requires(bool)
    isCollection = requires(bool)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    shadowing = definesIf(Context, doc='''
    @rtype: Context
    The element that this shadow element is based on.
    ''')
    shadowed = definesIf(Context, doc='''
    @rtype: Context
    The element that this element shadows.
    ''')
    # ---------------------------------------------------------------- Required
    property = requires(TypeProperty)
    
# --------------------------------------------------------------------

class InvokerShadowHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the shadow invokers that just have duty to capture data in
    the path mostly for accessible invokers.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Element=Element)
    
    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the shadow invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if not register.invokers: return  # No invoker to process
        assert isinstance(register.invokers, list), 'Invalid invokers %s' % register.invokers
        assert isinstance(register.doCopyInvoker, IDo), 'Invalid copy invoker %s' % register.doCopyInvoker
        assert isinstance(register.doCopyElement, IDo), 'Invalid copy element %s' % register.doCopyElement
        
        # First we grab all collections that have a property input.
        collections = []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.methodHTTP != HTTP_GET or invoker.isModel or not invoker.isCollection or not invoker.path: continue
            for el in invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if el.property:
                    collections.append(invoker)
                    break
            
        if not collections: return

        ninvokers = []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.methodHTTP != HTTP_GET or invoker.isCollection or not invoker.isModel or not invoker.path: continue
            
            for cinvoker in collections:
                assert isinstance(cinvoker, Invoker), 'Invalid invoker %s' % cinvoker
                
                invokerId = '(%s shadowed %s)' % (invoker.id, cinvoker.id)
                if invokerId in register.exclude: continue
                path = self.merge(cinvoker.path, invoker.path, register.doCopyElement)
                if not path: continue
                
                shadow = invoker.__class__()
                assert isinstance(shadow, Invoker), 'Invalid invoker %s' % shadow
                shadow.id = invokerId
                shadow.path = path
                shadow.shadowing = invoker
                if Invoker.shadowed in shadow: shadow.shadowed = cinvoker
                register.doCopyInvoker(shadow, invoker)
                
                ninvokers.append(shadow)
                 
        register.invokers.extend(ninvokers)
        
    # ----------------------------------------------------------------
    
    def merge(self, cpath, gpath, copyElement):
        '''
        Merges the collection path with the get path.
        '''
        assert isinstance(cpath, list), 'Invalid collection path %s' % cpath
        assert isinstance(gpath, list), 'Invalid get path %s' % gpath
        assert isinstance(copyElement, IDo), 'Invalid copy element %s' % copyElement
        
        path = []
        for gel in gpath:
            assert isinstance(gel, Element), 'Invalid element %s' % gel
            if not gel.property: continue
            for cel in cpath:
                assert isinstance(cel, Element), 'Invalid element %s' % cel
                if not cel.property: continue
                if isCompatible(gel.property, cel.property): return
        
        for el in cpath:
            sel = copyElement(el.__class__(), el)
            if Element.shadowed in sel: sel.shadowed = el
            path.append(sel)
            
        for el in gpath:
            sel = copyElement(el.__class__(), el)
            if Element.shadowing in sel: sel.shadowing = el
            path.append(sel)
            
        return path

# --------------------------------------------------------------------

class RegisterNodes(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    nodes = requires(list)

class InvokerShadow(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    shadowing = requires(Context)
    
class NodeConflict(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    conflicts = requires(dict)

# --------------------------------------------------------------------

class ConflictShadowHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the node invokers conflict resolving for shadow invokers.
    '''
    
    def __init__(self):
        super().__init__(Invoker=InvokerShadow, Node=NodeConflict)

    def process(self, chain, register:RegisterNodes, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the shdow conflict resolving.
        '''
        assert isinstance(register, RegisterNodes), 'Invalid register %s' % register
        if not register.nodes: return
        
        aborted = []
        for node in register.nodes:
            assert isinstance(node, NodeConflict), 'Invalid node %s' % node
            if not node.conflicts: continue
            assert isinstance(node.conflicts, dict), 'Invalid conflicts %s' % node.conflicts
            
            for invokers in node.conflicts.values():
                assert isinstance(invokers, list), 'Invalid invokers %s' % invokers
                k = 0
                while k < len(invokers) and len(invokers) > 1:
                    invoker = invokers[k]
                    k += 1
                    assert isinstance(invoker, InvokerShadow), 'Invalid invoker %s' % invoker
                    if invoker.shadowing:
                        aborted.append(invoker)
                        k -= 1
                        del invokers[k]
        
        if aborted: raise Abort(*aborted)

# --------------------------------------------------------------------

class InvokerRequired(InvokerShadow):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    
class NodeRequired(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    invokersAccessible = requires(list)
    
# --------------------------------------------------------------------

class RequiredShadowHandler(HandlerProcessor):
    '''
    Implementation for a processor that checks if a shadow is required.
    '''
    
    def __init__(self):
        super().__init__(Invoker=InvokerRequired, Node=NodeRequired)

    def process(self, chain, register:RegisterNodes, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Check if the shadows are required.
        '''
        assert isinstance(register, RegisterNodes), 'Invalid register %s' % register
        if not register.nodes: return
        
        aborted = []
        for node in register.nodes:
            assert isinstance(node, NodeRequired), 'Invalid node %s' % node
            if not node.invokers or HTTP_GET not in node.invokers: continue
            invoker = node.invokers[HTTP_GET]
            assert isinstance(invoker, InvokerRequired), 'Invalid invoker %s' % invoker
            if not invoker.shadowing: continue
            assert isinstance(invoker.shadowing, InvokerRequired), 'Invalid invoker %s' % invoker.shadowing
            assert isinstance(invoker.shadowing.node, NodeRequired), 'Invalid node %s' % invoker.shadowing.node
            
            if not node.invokersAccessible: aborted.append(invoker)
            else:
                assert isinstance(node.invokersAccessible, list), 'Invalid accessible invokers %s' % node.invokersAccessible
                if invoker.shadowing.node.invokersAccessible:
                    node.invokersAccessible.reverse()
                    node.invokersAccessible.extend(invoker.shadowing.node.invokersAccessible)
                    node.invokersAccessible.reverse()
        
        if aborted: raise Abort(*aborted)
