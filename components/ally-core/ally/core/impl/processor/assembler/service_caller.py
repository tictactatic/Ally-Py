'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the callers created based on services.
'''

from ally.api.operator.container import Service, Call
from ally.api.operator.type import TypeService
from ally.api.type import typeFor
from ally.core.impl.invoker import InvokerCall
from ally.core.spec.resources import Invoker
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_sys import locationStack
from collections import Iterable

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    callers = defines(list, doc='''
    @rtype: list[Caller]
    The callers created based on the services.
    ''')
    # ---------------------------------------------------------------- Required
    services = requires(Iterable, doc='''
    @rtype: Iterable(class)
    The classes that implement service APIs.
    ''')
    
class CallerRegister(Context):
    '''
    The register caller context.
    '''
    # ---------------------------------------------------------------- Defined
    service = defines(TypeService, doc='''
    @rtype: TypeService
    The service type that owns the invoker.
    ''')
    invoker = defines(Invoker, doc='''
    @rtype: Invoker
    The invoker to be registered.
    ''')
    location = defines(str, doc='''
    @rtype: string
    The location string to localize the API call.
    ''')

# --------------------------------------------------------------------

class ServiceCallerHandler(HandlerProcessor):
    '''
    Implementation for a processor that creates invokers based on service implementations.
    '''

    def process(self, chain, register:Register, Caller:CallerRegister, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the invoking to be registered based on services.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Caller, CallerRegister), 'Invalid caller register class %s' % Caller
        assert isinstance(register.services, Iterable), 'Invalid services %s' % register.services

        if register.callers is None: register.callers = []
        for implementation in register.services:
            typeService = typeFor(implementation)
            assert isinstance(typeService, TypeService), 'Invalid service implementation %s' % implementation
            assert isinstance(typeService.service, Service), 'Invalid service %s' % typeService.service
    
            for call in typeService.service.calls.values():
                assert isinstance(call, Call), 'Invalid call %s' % call
                
                caller = Caller()
                register.callers.append(caller)
                assert isinstance(caller, CallerRegister), 'Invalid caller %s' % caller
                caller.service = typeService
                caller.invoker = InvokerCall(implementation, call)
                caller.location = locationStack(getattr(typeService.clazz, call.name))
                
