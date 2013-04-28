'''
Created on Apr 25, 2013

@package: ally indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the stream support for modifications performs.
'''

from ally.support.util_io import IInputStreamCT, IInputStream, tellPosition, \
    IClosable
from io import BytesIO

# --------------------------------------------------------------------

class ModifierStream(IInputStreamCT):
    '''
    Provides a stream that allows for modifications.
    '''
    __slots__ = ('_stream', '_record', '_rewind')
    
    def __init__(self, stream):
        '''
        Construct the rewinding stream.
        
        @param stream: IInputStream
            The input stream to wrap.
        '''
        assert isinstance(stream, IInputStream), 'Invalid stream %s' % stream
        
        self._stream = tellPosition(stream)
        self._record = None
        self._rewind = None
    
    def read(self, nbytes=None):
        '''
        @see: IInputStreamCT.read
        '''
        if nbytes:
            assert isinstance(nbytes, int), 'Invalid number of bytes required %s' % nbytes
            if nbytes < 0: nbytes = None
            elif nbytes == 0: return b''
            
        if nbytes is None:
            if self._rewind is not None:
                byts = b''.join((self._rewind, self._stream.read()))
                self._rewind = None
            else: byts = self._stream.read()
        elif self._rewind is not None:
            if len(self._rewind) >= nbytes:
                byts = self._rewind[:nbytes]
                self._rewind = self._rewind[nbytes:]
            else:
                byts = b''.join((self._rewind, self._stream.read(nbytes - len(self._rewind))))
                self._rewind = None
        else: byts = self._stream.read(nbytes) 
            
        if self._record is not None:
            self._record.write(byts)
        
        return byts
            
    def tell(self):
        '''
        @see: IInputStreamCT.tell
        '''
        if self._rewind is None: return self._stream.tell()
        return self._stream.tell() - len(self._rewind)
        
    def close(self):
        '''
        @see: IInputStreamCT.close
        '''
        self._record = None
        self._rewind = None
        if isinstance(self._stream, IClosable): self._stream.close()
        
    # ----------------------------------------------------------------
        
    def discard(self, until):
        '''
        Discard from the stream bytes until the tell method equals with the until value.
        
        @param until: integer
            The position until to discard bytes.
        '''
        assert isinstance(until, int), 'Invalid until offset %s' % until
        
        if until <= self.tell(): return
        nbytes = until - self.tell()
        
        # Discarding 1 kilo at a time.
        while nbytes > 0:
            if nbytes <= 1024: block = self.read(nbytes)
            else: block = self.read(1024)
            if block == b'': raise IOError('The stream is missing %s bytes' % nbytes)
            nbytes -= len(block)
            
    # ----------------------------------------------------------------
    
    def record(self):
        '''
        Start to record all the bytes processed with this stream.
        '''
        if self._record is None: self._record = BytesIO()
        
    def rewind(self):
        '''
        Stops the recording and rewind all recorded bytes back into the stream.
        '''
        if self._record is not None:
            self._rewind = self._record.getvalue()
            self._record = None
        
    def stop(self):
        '''
        Stop the recording and discard all recorded bytes.
        '''
        self._record = None
