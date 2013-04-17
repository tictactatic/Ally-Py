'''
Created on Apr 12, 2012

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides assemblage markers.
'''

from ally.assemblage.http.spec.assemblage import Marker
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import RequestHTTP, ResponseHTTP, ResponseContentHTTP, \
    HTTP_GET, HTTP
from ally.support.util_io import IInputStream
from io import BytesIO
from urllib.parse import urlparse, parse_qsl
import codecs
import json
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    markers = defines(dict, doc='''
    @rtype: dictionary{integer: Marker}
    The markers indexed by id.
    ''')

# --------------------------------------------------------------------

class RequestMarker(RequestHTTP):
    '''
    The request marker context.
    '''
    # ---------------------------------------------------------------- Defined
    accTypes = defines(list)
    accCharSets = defines(list)

# --------------------------------------------------------------------

@injected
class MarkerHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the markers by using REST data received from either internal or
    external server. The Marker structure is defined as in the @see: assemblage plugin. If there are no markers this
    handler will stop the chain.
    '''
    
    scheme = HTTP
    # The scheme to be used in fetching the Gateway objects.
    mimeTypeJson = 'json'
    # The json mime type to be sent for the gateway requests.
    encodingJson = 'utf-8'
    # The json encoding to be sent for the gateway requests.
    uri = str
    # The URI used in fetching the gateways.
    assembly = Assembly
    # The assembly to be used in processing the request for the gateways.
    
    def __init__(self):
        assert isinstance(self.scheme, str), 'Invalid scheme %s' % self.scheme
        assert isinstance(self.mimeTypeJson, str), 'Invalid json mime type %s' % self.mimeTypeJson
        assert isinstance(self.encodingJson, str), 'Invalid json encoding %s' % self.encodingJson
        assert isinstance(self.uri, str), 'Invalid URI %s' % self.uri
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Branch(self.assembly).using('requestCnt', 'response', 'responseCnt', request=RequestMarker))
        
        self._markers = None

    def process(self, chain, processing, assemblage:Assemblage, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Obtains the markers.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        
        if self._markers is None:
            request = processing.ctx.request()
            assert isinstance(request, RequestMarker), 'Invalid request %s' % request
            url = urlparse(self.uri)
            request.scheme, request.method = self.scheme, HTTP_GET
            request.headers = {}
            request.uri = url.path.lstrip('/')
            request.parameters = parse_qsl(url.query, True, False)
            request.accTypes = [self.mimeTypeJson]
            request.accCharSets = [self.encodingJson]
            
            chainMarker = Chain(processing)
            chainMarker.process(**processing.fillIn(request=request)).doAll()
    
            response, responseCnt = chainMarker.arg.response, chainMarker.arg.responseCnt
            assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
            assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
            
            if ResponseHTTP.text in response and response.text: text = response.text
            elif ResponseHTTP.code in response and response.code: text = response.code
            else: text = None
            if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None or not isSuccess(response.status):
                log.error('Cannot fetch markers from \'%s\' because %s %s', self.uri, response.status, text)
                return
            
            if isinstance(responseCnt.source, IInputStream):
                source = responseCnt.source
            else:
                source = BytesIO()
                for bytes in responseCnt.source: source.write(bytes)
                source.seek(0)
            mobjs = json.load(codecs.getreader(self.encodingJson)(source))
            
            assert isinstance(mobjs, dict), 'Invalid objects %s' % mobjs
            assert 'MarkerList' in mobjs, 'Invalid objects %s, no MarkerList' % mobjs
            
            self._markers = [Marker(obj) for obj in mobjs['MarkerList']]
        
        if assemblage.markers is None: assemblage.markers = {}
        assemblage.markers.update((marker.id, marker) for marker in self._markers)
        
        chain.proceed()
        
