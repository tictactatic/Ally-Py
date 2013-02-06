'''
Created on Nov 24, 2011

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from ally.container import ioc
from ally.design.processor import Handler, Assembly
from ally.http.impl.processor.deliver_code import DeliverCodeHandler
from ally.http.impl.processor.header import HeaderHandler
from ally.http.impl.processor.headers.allow import AllowEncodeHandler
from ally.http.impl.processor.headers.content_length import \
    ContentLengthDecodeHandler, ContentLengthEncodeHandler
from ally.http.impl.processor.headers.content_type import \
    ContentTypeDecodeHandler, ContentTypeEncodeHandler
from ally.http.impl.processor.internal_error import InternalErrorHandler
from ally.http.impl.processor.method_override import MethodOverrideHandler
from ally.http.impl.processor.path_encoder import EncoderPathHandler
from ally.http.spec.codes import PATH_NOT_FOUND

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.config
def read_from_params():
    '''If true will also read header values that are provided as query parameters'''
    return True

# --------------------------------------------------------------------

@ioc.entity
def internalError(): return InternalErrorHandler()

@ioc.entity
def header() -> Handler:
    b = HeaderHandler()
    b.useParameters = read_from_params()
    return b

# --------------------------------------------------------------------
# Header decoders

@ioc.entity
def contentTypeDecode() -> Handler: return ContentTypeDecodeHandler()

@ioc.entity
def contentLengthDecode() -> Handler: return ContentLengthDecodeHandler()

# --------------------------------------------------------------------
# Header encoders

@ioc.entity
def contentTypeEncode() -> Handler: return ContentTypeEncodeHandler()

@ioc.entity
def contentLengthEncode() -> Handler: return ContentLengthEncodeHandler()

# --------------------------------------------------------------------
# General HTTP handlers

@ioc.entity
def methodOverride() -> Handler: return MethodOverrideHandler()

@ioc.entity
def encoderPath() -> Handler: return EncoderPathHandler()

@ioc.entity
def allowEncode() -> Handler: return AllowEncodeHandler()

@ioc.entity
def deliverNotFound() -> Handler:
    b = DeliverCodeHandler()
    b.code, b.status, b.isSuccess = PATH_NOT_FOUND
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyNotFound() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing a not found request.
    '''
    return Assembly()

# --------------------------------------------------------------------

@ioc.before(assemblyNotFound)
def updateAssemblyNotFound():
    assemblyNotFound().add(deliverNotFound())
