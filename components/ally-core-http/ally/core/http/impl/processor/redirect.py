'''
Created on Apr 12, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content location redirect based on references.
'''

from ally.api.operator.type import TypeModelProperty
from ally.api.type import TypeReference
from ally.container.ioc import injected
from ally.core.http.spec.codes import REDIRECT
from ally.core.http.spec.headers import LOCATION
from ally.core.spec.resources import Invoker
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
from ally.http.spec.codes import CodedHTTP
from ally.http.spec.headers import HeadersDefines
from ally.http.spec.server import IEncoderPath
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)

class Response(CodedHTTP, HeadersDefines):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    encoderPath = requires(IEncoderPath)
    obj = requires(object)

# --------------------------------------------------------------------

@injected
class RedirectHandler(HandlerBranching):
    '''
    Implementation for a processor that provides the redirect by using the content location based on found references.
    '''
    
    redirectAssembly = Assembly
    # The redirect processors, among this processors it has to be one to fetch the location object.

    def __init__(self):
        assert isinstance(self.redirectAssembly, Assembly), 'Invalid redirect assembly %s' % self.redirectAssembly
        super().__init__(Branch(self.redirectAssembly).included())

    def process(self, chain, redirect, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the redirect.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(redirect, Processing), 'Invalid processing %s' % redirect
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        if response.isSuccess is not False:  # Skip in case the response is in error
            assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker
            assert isinstance(response.encoderPath, IEncoderPath), 'Invalid encoder path %s' % response.encoderPath

            typ = request.invoker.output
            if isinstance(typ, TypeModelProperty): typ = typ.type
            if isinstance(typ, TypeReference): chain.route(redirect).onFinalize(self.processFinalize)
                
    def processFinalize(self, final, response, **keyargs):
        '''
        Populate the redirect.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if response.isSuccess is not False:
            LOCATION.put(response, response.encoderPath.encode(response.obj))
            REDIRECT.set(response)
