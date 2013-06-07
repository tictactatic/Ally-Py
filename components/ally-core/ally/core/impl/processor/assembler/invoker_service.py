'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invokers created based on services.
'''

from ally.api.operator.container import Service, Call
from ally.api.operator.type import TypeService
from ally.api.type import typeFor, Type
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_sys import locationStack
from collections import Iterable, Callable

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    invokers = defines(list, doc='''
    @rtype: list[Context]
    The invokers created based on the services.
    ''')
    # ---------------------------------------------------------------- Required
    services = requires(Iterable)
    
class InvokerCall(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    invoke = defines(Callable, doc='''
    @rtype: Callable
    The invoke used for handling the request.
    ''')
    service = defines(TypeService, doc='''
    @rtype: TypeService
    The invoker service.
    ''')
    call = defines(Call, doc='''
    @rtype: Call
    The call of the invoker.
    ''')
    method = defines(int, doc='''
    @rtype: integer
    The invoker method.
    ''')
    inputs = defines(tuple, doc='''
    @rtype: tuple(Input)
    The tuple of inputs required for the call.
    ''')
    output = defines(Type, doc='''
    @rtype: Type
    The output type of the call.
    ''')
    location = defines(str, doc='''
    @rtype: string
    The location string to localize the API call.
    ''')

# --------------------------------------------------------------------

class InvokerServiceHandler(HandlerProcessor):
    '''
    Implementation for a processor that creates invokers based on service implementations.
    '''

    def process(self, chain, register:Register, Invoker:InvokerCall, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the invokers to be registered based on services.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Invoker, InvokerCall), 'Invalid invoker %s' % Invoker
        assert isinstance(register.services, Iterable), 'Invalid services %s' % register.services

        if register.invokers is None: register.invokers = []
        for implementation in register.services:
            service = typeFor(implementation)
            assert isinstance(service, TypeService), 'Invalid service implementation %s' % implementation
            assert isinstance(service.service, Service), 'Invalid service %s' % service.service
    
            for call in service.service.calls.values():
                assert isinstance(call, Call), 'Invalid call %s' % call
                
                invoker = Invoker()
                assert isinstance(invoker, InvokerCall), 'Invalid invoker %s' % invoker
                invoker.invoke = getattr(implementation, call.name)
                invoker.service = service
                invoker.call = call
                invoker.method = call.method
                invoker.inputs = call.inputs
                invoker.output = call.output
                invoker.location = locationStack(getattr(service.clazz, call.name))
                register.invokers.append(invoker)
