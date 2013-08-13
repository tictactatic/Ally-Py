'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the filter calls processing.
'''

from ally.api.config import GET
from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import Call, Type, typeFor
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.filter import Allowed
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    filters = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The filter contexts indexed by name.
    ''')
    hintsCall = definesIf(dict)
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list, doc='''
    @rtype: list[Context]
    The starting path elements for filter.
    ''')
    # ---------------------------------------------------------------- Required
    call = requires(Call)
    method = requires(int)
    output = requires(Type)
    location = requires(str)
    
class ElementFilter(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The element name.
    ''')
    model = defines(TypeModel, doc='''
    @rtype: TypeModel
    The model represented by the element.
    ''')
        
class ACLFilterInvoker(Context):
    '''
    The ACL filter context.
    '''
    # ---------------------------------------------------------------- Defined
    invokers = defines(list, doc='''
    @rtype: list[Context]
    The invoker contexts associated with the filter.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='processFilter')
class ProcessFilterHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the filter calls processing.
    '''
    
    hintName = 'filter'
    # The hint name for the call filter.
    hintDescription = '(string) The filter name to associate with the filter call, the filter calls are specially managed '\
    'by the container, the sole purpose of this type of calls is to validate resources and should not be used as part of '\
    'the main API.'
    # The hint description.
    typeModelAllowed = typeFor(Allowed)
    # The allowed model to associate with filters.
    typePropertyAllowed = typeFor(Allowed.IsAllowed)
    # The is allowed property to associate with the return type for filters.
    
    def __init__(self):
        assert isinstance(self.hintName, str), 'Invalid hint name %s' % self.hintName
        assert isinstance(self.hintDescription, str), 'Invalid hint description %s' % self.hintDescription
        assert isinstance(self.typeModelAllowed, TypeModel), 'Invalid type model allowed %s' % self.typeModelAllowed
        assert isinstance(self.typePropertyAllowed, TypeProperty), \
        'Invalid type property allowed %s' % self.typePropertyAllowed
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:Register, ACLFilter:ACLFilterInvoker, Element:ElementFilter, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the filter calls.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(ACLFilter, ACLFilterInvoker), 'Invalid filter class %s' % ACLFilter
        assert issubclass(Element, ElementFilter), 'Invalid path element %s' % Element
        if not register.invokers: return
        
        if Register.hintsCall in register:
            if register.hintsCall is None: register.hintsCall = {}
            register.hintsCall[self.hintName] = self.hintDescription
            
        aborted = []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.call: continue  # No call to process hints on.
            assert isinstance(invoker.call, Call), 'Invalid call %s' % invoker.call
            if not self.hintName in invoker.call.hints: continue
            
            filterName = invoker.call.hints[self.hintName]
            if not isinstance(filterName, str) and filterName:
                log.error('Cannot use because invalid filter name \'%s\', expected a string value with at '
                          'least one character, at:%s', filterName, invoker.location)
                aborted.append(invoker)
                continue
            
            if not invoker.method == GET:
                log.error('Cannot use because filter call needs to be a GET call, at:%s', invoker.location)
                aborted.append(invoker)
                continue
            
            assert isinstance(invoker.output, Type), 'Invalid output %s' % invoker.output
            if not invoker.output.isOf(bool):
                log.error('Cannot use because filter call has invalid output \'%s\', expected a boolean return, at:%s',
                          invoker.output, invoker.location)
                aborted.append(invoker)
                continue
            
            if invoker.path is None: invoker.path = []
            invoker.path.insert(0, Element(name=self.typeModelAllowed.name, model=self.typeModelAllowed))
            invoker.output = self.typePropertyAllowed
            
            if register.filters is None: register.filters = {}
            aclFilter = register.filters.get(filterName)
            if aclFilter is None: aclFilter = register.filters[filterName] = ACLFilter()
            assert isinstance(aclFilter, ACLFilterInvoker), 'Invalid filter %s' % aclFilter
            
            if aclFilter.invokers is None: aclFilter.invokers = []
            aclFilter.invokers.append(invoker)
        
        if aborted: raise Abort(*aborted)
