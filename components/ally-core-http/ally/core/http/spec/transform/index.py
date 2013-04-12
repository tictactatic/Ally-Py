'''
Created on Apr 4, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides additional indexing data.
'''

from ally.core.spec.transform.index import IMarkRegistry, REFERENCE, DO_CAPTURE

# --------------------------------------------------------------------

HTTP_URL = 'URL'  # Indicates an HTTP URL to follow.

# --------------------------------------------------------------------

def registerDefaultMarks(registry):
    '''
    Register the default markers defined in this module.
    
    @param registry: IMarkRegistry
        The registry to push the marks in.
    '''
    assert isinstance(registry, IMarkRegistry), 'Invalid registry %s' % registry
    
    registry.register(HTTP_URL, action=REFERENCE, do=DO_CAPTURE)
    # The HTTP URL reference capture.
