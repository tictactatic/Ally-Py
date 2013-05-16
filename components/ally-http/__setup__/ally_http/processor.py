'''
Created on Nov 24, 2011

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from ally.container import ioc
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.http.impl.processor.chunked_transfer import \
    ChunkedTransferEncodingHandler
from ally.http.impl.processor.connection import ConnectionCloseHandler, \
    ConnectionHandler
from ally.http.impl.processor.deliver_code import DeliverCodeHandler
from ally.http.impl.processor.headers.accept import AcceptRequestDecodeHandler, \
    AcceptRequestEncodeHandler
from ally.http.impl.processor.headers.allow import AllowEncodeHandler
from ally.http.impl.processor.headers.content_length import \
    ContentLengthDecodeHandler, ContentLengthEncodeHandler
from ally.http.impl.processor.headers.content_type import \
    ContentTypeRequestDecodeHandler, ContentTypeResponseEncodeHandler, \
    ContentTypeResponseDecodeHandler
from ally.http.impl.processor.internal_error import InternalErrorHandler
from ally.http.impl.processor.method_override import MethodOverrideHandler, \
    MethodOverrideAllowHandler
from ally.http.impl.processor.path_encoder import EncoderPathHandler
from ally.http.spec.codes import PATH_NOT_FOUND

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.entity
def internalError(): return InternalErrorHandler()

@ioc.entity
def acceptRequestDecode() -> Handler: return AcceptRequestDecodeHandler()

@ioc.entity
def acceptRequestEncode() -> Handler: return AcceptRequestEncodeHandler()

@ioc.entity
def contentTypeRequestDecode() -> Handler: return ContentTypeRequestDecodeHandler()

@ioc.entity
def contentTypeResponseDecode() -> Handler: return ContentTypeResponseDecodeHandler()

@ioc.entity
def contentTypeResponseEncode() -> Handler: return ContentTypeResponseEncodeHandler()

@ioc.entity
def contentLengthDecode() -> Handler: return ContentLengthDecodeHandler()

@ioc.entity
def contentLengthEncode() -> Handler: return ContentLengthEncodeHandler()

@ioc.entity
def chunkedTransferEncoding(): return ChunkedTransferEncodingHandler()

@ioc.entity
def methodOverride() -> Handler: return MethodOverrideHandler()

@ioc.entity
def methodOverrideAllow() -> Handler: return MethodOverrideAllowHandler()

@ioc.entity
def encoderPath() -> Handler: return EncoderPathHandler()

@ioc.entity
def allowEncode() -> Handler: return AllowEncodeHandler()

@ioc.entity
def deliverNotFound() -> Handler:
    b = DeliverCodeHandler()
    b.code = PATH_NOT_FOUND
    return b

@ioc.entity
def connectionClose() -> Handler: return ConnectionCloseHandler()

@ioc.entity
def connection() -> Handler: return ConnectionHandler()

# --------------------------------------------------------------------

@ioc.entity
def assemblyNotFound() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing a not found request.
    '''
    return Assembly('Not found')

# --------------------------------------------------------------------

@ioc.before(assemblyNotFound)
def updateAssemblyNotFound():
    assemblyNotFound().add(deliverNotFound())
