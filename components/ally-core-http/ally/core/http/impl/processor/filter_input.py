'''
Created on Aug 23, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the input filter handler.
'''

from ally.api.error import InputError
from ally.api.type import Input
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP, FORBIDDEN_ACCESS, BAD_GATEWAY
from ally.http.spec.headers import HeaderCmx
from ally.internationalization import _
from ally.support.http.request import RequesterGetJSON
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

HEADER_FILTER_INPUT = HeaderCmx('Filter-Input', True)
# The header name used to place the input filter.
PROPERTY_NAME = 'Property'
# The header filter input value associated with properties.

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    modelInput = requires(Input)
        
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    arguments = requires(dict)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorInput = defines(InputError, doc='''
    @rtype: InputError
    The input error associated with a forbidden access.
    ''')
    
# --------------------------------------------------------------------

@injected
class FilterInputHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the input filter handler.
    '''
    
    requesterGetJSON = RequesterGetJSON
    # The requester for getting the filters.

    def __init__(self):
        assert isinstance(self.requesterGetJSON, RequesterGetJSON), 'Invalid requester JSON %s' % self.requesterGetJSON
        super().__init__(Invoker=Invoker)

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Filter the input based on received specifications.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error
        
        if not request.arguments: return
        
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.modelInput: return
        
        filters = HEADER_FILTER_INPUT.decode(request)
        if not filters: return
        
        assert isinstance(request.invoker.modelInput, Input), 'Invalid input %s' % request.invoker.modelInput
        assert isinstance(request.arguments, dict), 'Invalid arguments %s' % request.arguments
        model = request.arguments.get(request.invoker.modelInput.name)
        if model is None: return
        
        for item in filters:
            if not isinstance(item, tuple): continue
            name, pfilters = item
            if name != PROPERTY_NAME: continue
            assert isinstance(pfilters, dict), 'Invalid property filters %s' % pfilters
            
            for name, paths in pfilters.items():
                try: value = getattr(model, name)
                except AttributeError:
                    log.warn('Invalid filter property name \'%s\' for %s', name, model)
                    continue
                if value is None: continue
                value = str(value)
                for path in paths.split('|'):
                    jobj, error = self.requesterGetJSON.request(path.replace('*', value), details=True)
                    if jobj is None:
                        BAD_GATEWAY.set(response)
                        response.text = error.text
                        return
                
                    if jobj['IsAllowed'] == True: break
                    
                else:
                    FORBIDDEN_ACCESS.set(response)
                    response.errorInput = InputError(_('Provided value is not allowed'), getattr(model.__class__, name))
                    return
            break
                
