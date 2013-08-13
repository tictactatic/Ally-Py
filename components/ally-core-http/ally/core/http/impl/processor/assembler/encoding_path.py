'''
Created on Jul 31, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path encoder.
'''
# TODO: Gabrile: Move to encoders when they are refactored
from ally.api.operator.type import TypeProperty
from ally.api.type import Type
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo
from urllib.parse import quote
from ally.core.impl.processor.encoder.base import ExportingSupport

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    hasMandatorySlash = requires(bool)
    type = requires(Type)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    doEncodePath = defines(IDo, doc='''
    @rtype: callable(support:Context=None) -> string
    The path encoder that takes as arguments the support context if any required, returns the encoded path.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(list)
    isCollection = requires(bool)
    node = requires(Context)
    
class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)
    node = requires(Context)
    
class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Optional
    extension = optional(str)
    rootURI = optional(str)
    converterPath = optional(Converter)
    nodesValues = optional(dict)
    doEncodePath = optional(IDo)
        
# --------------------------------------------------------------------

encodingPathExport = ExportingSupport(Support)
# The encoding path support export.

class EncodingPathHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the path encoding.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Node=Node, Element=Element)
    
    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the path encoder.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invoker to process

        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            elements = []
            for el in invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if el.property:
                    assert isinstance(el.node, Node), 'Invalid element node %s' % el.node
                    elements.append(el.node)
                else:
                    assert isinstance(el.name, str) and el.name, 'Invalid element name %s' % el.name
                    elements.append(el.name)
            
            if invoker.isCollection: elements.append('')
            elif invoker.node:
                assert isinstance(invoker.node, Node), 'Invalid node %s' % invoker.node
                if invoker.node.hasMandatorySlash: elements.append('')
            
            invoker.doEncodePath = self.createEncode(elements)

    # ----------------------------------------------------------------
    
    def createEncode(self, elements):
        '''
        Create the path encode.
        '''
        assert isinstance(elements, list), 'Invalid elements %s' % elements
        def doEncodePath(support=None):
            '''
            Do encode the path.
            '''
            path = []
            for el in elements:
                if isinstance(el, str): path.append(el)
                else:
                    assert isinstance(el, Node), 'Invalid node %s' % el
                    assert isinstance(support, Support), 'Invalid support %s' % support
                    assert Support.converterPath in support, 'Converter required in %s' % support
                    assert isinstance(support.converterPath, Converter), 'Invalid converter %s' % support.converterPath
                    assert Support.nodesValues in support, 'Node values required in %s' % support
                    assert isinstance(support.nodesValues, dict), 'Invalid node values %s' % support.nodesValues
                    
                    assert el in support.nodesValues, 'No value could be found for %s' % el
                    value = support.nodesValues[el]
                    if not isinstance(value, str): value = support.converterPath.asString(value, el.type)
                    path.append(quote(value, safe=''))
            
            if Support.rootURI in support and support.rootURI: path.insert(0, support.rootURI)
            uri = '/'.join(path)
            if Support.extension in support and support.extension: uri = '%s.%s' % (uri, support.extension)
            if Support.doEncodePath in support and support.doEncodePath: uri = support.doEncodePath(uri)
            
            return uri
        return doEncodePath
