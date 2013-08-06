'''
Created on Aug 28, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the text parser processor handler.
'''

from . import base
from .base import ParseBaseHandler, Target
from ally.container.ioc import injected
from ally.core.impl.processor.decoder.base import addFailure
from ally.design.processor.attribute import requires
from ally.support.util_io import IInputStream
from ally.support.util_spec import IDo
from collections import Callable

# --------------------------------------------------------------------

class Decoding(base.Decoding):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    doDecode = requires(IDo)
    
# --------------------------------------------------------------------

@injected
class ParseTextHandler(ParseBaseHandler):
    '''
    Provides the text parsing.
    @see: ParseBaseHandler
    '''

    parser = Callable
    # A Callable(file, string) function used for decoding a bytes file to a text object.

    def __init__(self):
        assert callable(self.parser), 'Invalid callable parser %s' % self.parser
        super().__init__()

        self.contentType = next(iter(self.contentTypes))

    def parse(self, source, charSet, decoding, target):
        '''
        @see: ParseBaseHandler.parse
        '''
        assert isinstance(source, IInputStream), 'Invalid stream %s' % source
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(target, Target), 'Invalid target %s' % target
        assert callable(decoding.doDecode), 'Invalid decoding %s' % decoding.doDecode

        try: obj = self.parser(source, charSet)
        except ValueError as e: addFailure(target, decoding, str(e))
        else: decoding.doDecode(target, obj)
