'''
Created on May 14, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the profiler presenting.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP, PATH_FOUND
from ally.support.util_io import IInputStream
from collections import Iterable
from io import StringIO
import logging
import pstats

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    parameters = requires(list)
    
class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    headers = defines(dict)
    
class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Optional
    source = defines(IInputStream, Iterable)
    length = defines(int)

# --------------------------------------------------------------------

@injected
class ProfilerViewHandlerHandler(HandlerProcessor):
    '''
    Implementation for a processor that present profiling data.
    '''
    
    profiler = None
    # The profile to be presented.
    headers = {'Content-Type':'text'}
    # The headers that will be placed on the response.

    def __init__(self):
        '''
        Construct the view profiler.
        '''
        assert self.profiler, 'Invalid profile %s' % self.profiler
        assert isinstance(self.headers, dict), 'Invalid headers %s' % self.headers
        super().__init__()

    def process(self, chain, request:Request, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        Provides the profiling.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        self.profiler.disable()
        
        sort, restrict, limit, what = [], [], 100, 'stats'
        if request.parameters:
            for pname, pvalue in request.parameters:
                if pname == 'sort': sort.extend(v.strip() for v in pvalue.split(','))
                elif pname == 'restrict': restrict.extend(v.strip() for v in pvalue.split(','))
                elif pname == 'what': what = pvalue
                elif pname == 'limit':
                    try: limit = int(pvalue)
                    except: pass
        
        restrict.append(limit)
        if not sort: sort.append('time')
        
        stream = StringIO()
        stats = pstats.Stats(self.profiler, stream=stream)
        try: stats.sort_stats(*sort)
        except:
            content = b'Invalid sort parameters'
        else:
            try: fun = getattr(stats, 'print_%s' % what)
            except:
                content = b'Invalid what parameter'
            else:
                try: fun(*restrict)
                except:
                    content = b'Invalid restrict parameters'
                else:
                    content = stream.getvalue().encode(encoding='utf-8', errors='backslashreplace')
        
        PATH_FOUND.set(response)
        response.headers = dict(self.headers)
        responseCnt.source = (content,)
        responseCnt.length = len(content)
        
        self.profiler.enable()
