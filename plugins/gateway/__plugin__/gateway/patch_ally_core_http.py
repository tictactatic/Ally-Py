'''
Created on Feb 19, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core http setup patch.
'''

from .service import asPattern, defaultGateways
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_core_http  # @UnusedImport
except ImportError: log.info('No ally core http component available, thus no need to create Gateway configurations based on it')
else:
    from __setup__.ally_core_http.processor_error import statusToCode
    from __setup__.ally_core_http.server import root_uri_resources, root_uri_errors, \
    server_provide_errors
    from ally.http.spec.codes import METHOD_NOT_AVAILABLE, PATH_NOT_FOUND, \
        UNAUTHORIZED_ACCESS, FORBIDDEN_ACCESS, INVALID_AUTHORIZATION
    from ally.http.spec.server import HTTP_OPTIONS
    
    @ioc.before(statusToCode)
    def updateStatusToCodeForGateway():
        statusToCode().update({
                               UNAUTHORIZED_ACCESS.status: UNAUTHORIZED_ACCESS,
                               FORBIDDEN_ACCESS.status: FORBIDDEN_ACCESS,
                               })
    
    @ioc.before(defaultGateways)
    def updateGatewayWithResourcesOptions():
        defaultGateways().extend([
        {
         'Name': 'allow_resources_OPTIONS',
         'Pattern': asPattern(root_uri_resources()),
         'Methods': [HTTP_OPTIONS],
         },
                                   ])
    
    @ioc.before(defaultGateways)
    def updateGatewayWithResourcesErrors():
        if server_provide_errors():
            defaultGateways().extend([
            # If path is not found then we try to dispatch a unauthorized access if the path is not
            # found in REST the default error will have priority over the unauthorized access
            {
             'Name': 'error_unauthorized_vs_not_found',
             'Pattern': asPattern(root_uri_resources()),
             'Errors': [PATH_NOT_FOUND.status],
             'Navigate': '%s/{1}?status=%s' % (root_uri_errors(), UNAUTHORIZED_ACCESS.status),
             },
            {
             'Name': 'error_unauthorized',
             'Pattern': asPattern(root_uri_resources()),
             'Errors': [INVALID_AUTHORIZATION.status, FORBIDDEN_ACCESS.status, METHOD_NOT_AVAILABLE.status],
             'Navigate': '%s/{1}' % root_uri_errors(),
             },
                                       ])
