'''
Created on Jul 8, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the asyncore web server based on the python build in http server and asyncore package.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import optional
from ally.design.processor.execution import Chain, Processing, FILL_ALL
from ally.http.spec.server import RequestHTTP, ResponseHTTP, RequestContentHTTP, \
    ResponseContentHTTP, HTTP
from ally.support.util_io import IInputStream, IClosable
from ally.support.util_spec import IDo
from asyncore import dispatcher, loop
from collections import deque
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse, parse_qsl
import logging
import socket

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class RequestContentHTTPAsyncore(RequestContentHTTP):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Optional
    doContentReader = optional(IDo)

# --------------------------------------------------------------------

class RequestHandler(dispatcher, BaseHTTPRequestHandler):
    '''
    Request handler implementation based on @see: async_chat and @see: BaseHTTPRequestHandler.
    The async chat request handler. It relays for the HTTP processing on the @see: BaseHTTPRequestHandler,
    and uses the async_chat to asynchronous communication.
    '''
    
    bufferSize = 10 * 1024
    # The buffer size used for reading and writing.
    maximumRequestSize = 1024 * 1024
    # The maximum request size, 1M
    requestTerminator = b'\r\n\r\n'
    # Terminator that signals the http request is complete 

    def __init__(self, request, address, server):
        '''
        Construct the request handler.
        
        @param request: socket
            The connection request socket.
        @param address: tuple(string, integer)
            The client address.
        @param server: AsyncServer
            The server that created the request.
        '''
        assert isinstance(server, AsyncServer), 'Invalid server %s' % server
        assert isinstance(address, tuple), 'Invalid address %s' % address
        dispatcher.__init__(self, request, map=server.map)
        
        self.client_address = address
        self.request = self.connection = request
        self.server = server
        
        self.server_version = server.serverVersion
        
        self._readCarry = None
        self.rfile = BytesIO()
        self._reader = None
        self._chain = None
        
        self.wfile = BytesIO()
        self._writeq = deque()
        
        self._readHeader()
        
    def handle_read(self):
        '''
        @see: dispatcher.handle_read
        '''
        try: data = self.recv(self.bufferSize)
        except socket.error:
            log.exception('Exception occurred while reading the content from \'%s\'' % self.connection)
            self.close()
            return
        if data is not None: self.handle_data(data)
    
    def writable(self):
        '''
        @see: dispatcher.writable
        '''
        return bool(self._writeq)
    
    def handle_write(self):
        '''
        @see: dispatcher.handle_write
        '''
        assert self._writeq, 'Nothing to write'
        
        data, close = BytesIO(), False
        while self._writeq and data.tell() < self.bufferSize:
            content = self._writeq.popleft()
            if content is None:
                if self.close_connection: close = True
                break
            if isinstance(content, (bytes, memoryview)): data.write(content)
            elif isinstance(content, IInputStream):
                assert isinstance(content, IInputStream)
                byts = content.read(self.bufferSize - data.tell())
                if byts == b'':
                    if isinstance(content, IClosable): content.close()
                    continue
                data.write(byts)
                self._writeq.appendleft(content)
            else:
                while data.tell() < self.bufferSize:
                    try: byts = next(content)
                    except StopIteration: break
                    data.write(byts)
        
        sent = self.send(data.getbuffer())
        
        if close: self.close()
        elif sent < data.tell():
            self._writeq.appendleft(data.getbuffer()[sent:])
            
    def handle_error(self):
        log.exception('A problem occurred in the server')
    
    def end_headers(self):
        '''
        @see: BaseHTTPRequestHandler.end_headers
        '''
        super().end_headers()
        self.wfile.seek(0)
        self._writeq.append(self.wfile)
        self.wfile = BytesIO()

    def log_message(self, format, *args):
        '''
        @see: BaseHTTPRequestHandler.log_message
        '''
        # TODO: see for a better solution for this, check for next python release
        # This is a fix: whenever a message is logged there is an attempt to find some sort of host name which
        # creates a big delay whenever the request is made from a non localhost client.
        assert log.debug(format, *args) or True

    # ----------------------------------------------------------------
    
    def _readHeader(self):
        '''
        Prepare for a new HTTP header read.
        '''
        self.requestline = 0
        self.rfile.seek(0)
        self.rfile.truncate()
            
        self.readable = self._isReadable
        self.handle_data = self._headerHandleData
        
    def _readContent(self):
        '''
        Prepare for a HTTP content header read.
        '''
        assert self._chain is not None, 'No chain available'
        assert self._reader is not None, 'No reader available'
        
        self.readable = self._contentReadable
        self.handle_data = self._contentHandleData
    
    def _readContinue(self):
        '''
        Continue if is the case to read data from client.
        '''
        if self.close_connection:
            self.readable = self._notReadable
            self.handle_data = None
        else: self._readHeader()
    
    # ----------------------------------------------------------------
    
    def _isReadable(self):
        '''
        @see: dispatcher.readable
        '''
        return True
      
    def _notReadable(self):
        '''
        @see: dispatcher.readable
        '''
        return False

    # ----------------------------------------------------------------
    
    def _headerHandleData(self, data):
        '''
        Handle the data as being part of the request.
        '''
        if self._readCarry is not None:
            data = self._readCarry + data
            self._readCarry = None
        index = data.find(self.requestTerminator)
        requestTerminatorLen = len(self.requestTerminator)
        
        if index >= 0:
            index += requestTerminatorLen 
            self.rfile.write(memoryview(data)[:index])
            self.rfile.seek(0)
            self.raw_requestline = self.rfile.readline()
            self.parse_request()
            
            self._process(self.command or '')
            
            if index < len(data) and self.handle_data: self.handle_data(data[index:])
        else:
            self._readCarry = data[-requestTerminatorLen:]
            self.rfile.write(memoryview(data)[:-requestTerminatorLen])
            
            if self.rfile.tell() > self.maximumRequestSize:
                # We need to make sure that the content length is set for HTTP/1.1.
                self.send_header('Content-Length', '0')
                self.send_response(400, 'Request to long')
                self.end_headers()
                self._writeq.append(None)
        
    # ----------------------------------------------------------------
    
    def _contentReadable(self):
        '''
        @see: dispatcher.readable
        '''
        return self._reader is not None
    
    def _contentHandleData(self, data):
        '''
        Handle the data as being part of the request.
        '''
        assert self._chain is not None, 'No chain available'
        assert self._reader is not None, 'No reader available'
        if self._readCarry is not None:
            data = self._readCarry + data
            self._readCarry = None
            
        ret = self._reader(data)
        if ret is not True:
            assert ret is None or isinstance(ret, bytes), 'Invalid return %s' % ret
            self._readCarry = ret
            chain = self._chain
            assert isinstance(chain, Chain), 'Invalid chain %s' % chain
            
            self._reader = None
            self._chain = None
            
            self._readContinue()
            chain.execute()

    # ----------------------------------------------------------------
    
    def _process(self, method):
        assert isinstance(method, str), 'Invalid method %s' % method
        proc = self.server.processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        request, requestCnt = proc.ctx.request(), proc.ctx.requestCnt()
        assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContentHTTP), 'Invalid request content %s' % requestCnt
        
        if RequestHTTP.clientIP in request: request.clientIP = self.client_address[0]
        url = urlparse(self.path)
        request.scheme, request.method = HTTP, method.upper()
        request.uri = url.path.lstrip('/')
        if RequestHTTP.headers in request: request.headers = dict(self.headers)
        if RequestHTTP.parameters in request: request.parameters = parse_qsl(url.query, True, False)

        chain = Chain(proc, FILL_ALL, request=request, requestCnt=requestCnt)
        chain.onFinalize(self._processRespond)
        
        if RequestContentHTTPAsyncore.doContentReader in requestCnt:
            while True:
                if not chain.do():
                    self._readContinue()
                    break
                if requestCnt.doContentReader:
                    assert callable(requestCnt.doContentReader), 'Invalid content reader %s' % requestCnt.doContentReader
                    self._chain, self._reader = chain, requestCnt.doContentReader
                    self._readContent()  # Now we proceed to read content stage
                    break
        else:
            self._readContinue()
            chain.execute()
            
    def _processRespond(self, final, response, responseCnt, **keyargs):
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        assert isinstance(response.status, int), 'Invalid response status code %s' % response.status
        
        if ResponseHTTP.text in response and response.text: text = response.text
        elif ResponseHTTP.code in response and response.code: text = response.code
        else: text = None
        
        if ResponseHTTP.headers in response and response.headers is not None:
            for name, value in response.headers.items(): self.send_header(name, value)
            
        self.send_response(response.status, text)
        self.end_headers()
        
        if ResponseContentHTTP.source in responseCnt and responseCnt.source is not None:
            self._writeq.append(responseCnt.source)
            
        self._writeq.append(None)

# --------------------------------------------------------------------

@injected
class AsyncServer(dispatcher):
    '''
    The asyncore server handling the connection.
    '''
    
    serverVersion = str
    # The server version name
    serverHost = str
    # The server address host
    serverPort = int
    # The server port
    requestHandlerFactory = RequestHandler
    # The factory that provides request handlers, takes as arguments the server, request socket
    # and client address.
    assembly = Assembly
    # The assembly used for resolving the requests
    
    timeout = 10.0
    # The timeout for select loop.

    def __init__(self):
        '''
        Construct the server.
        '''
        assert isinstance(self.serverVersion, str), 'Invalid server version %s' % self.serverVersion
        assert isinstance(self.serverHost, str), 'Invalid server host %s' % self.serverHost
        assert isinstance(self.serverPort, int), 'Invalid server port %s' % self.serverPort
        assert callable(self.requestHandlerFactory), 'Invalid request handler factory %s' % self.requestHandlerFactory
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.timeout, float), 'Invalid timeout %s' % self.timeout
        self.map = {}
        dispatcher.__init__(self, map=self.map)

        self.processing = self.assembly.create(request=RequestHTTP, requestCnt=RequestContentHTTPAsyncore,
                                               response=ResponseHTTP, responseCnt=ResponseContentHTTP)
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((self.serverHost, self.serverPort))
        self.listen(1024)  # lower this to 5 if your OS complains

    def handle_accept(self):
        '''
        @see: dispatcher.handle_accept
        '''
        try:
            request, address = self.accept()
        except socket.error:
            log.exception('A problem occurred while waiting connections')
            return
        except TypeError:
            log.exception('A EWOULDBLOCK problem occurred while waiting connections')
            return
        # creates an instance of the handler class to handle the request/response
        # on the incoming connection
        self.requestHandlerFactory(request, address, self)
    
    def serve_forever(self):
        '''
        Loops and servers the connections.
        '''
        loop(self.timeout, map=self.map)

# --------------------------------------------------------------------

def run(server):
    '''
    Run the asyncore server.
    
    @param server: AsyncServer
        The asyncore server to run.
    '''
    assert isinstance(server, AsyncServer), 'Invalid server %s' % server
        
    try:
        log.info('=' * 50 + ' Started Async HTTP server...')
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('=' * 50 + ' ^C received, shutting down server')
        server.close()
    except:
        log.exception('=' * 50 + ' The server has stooped')
        try: server.close()
        except: pass
