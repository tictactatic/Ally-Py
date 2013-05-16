'''
Created on Jun 21, 2012

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Method invoker testing.
'''

# Required in order to register the package extender whenever the unit test is run.
if True:
    import package_extender
    package_extender.PACKAGE_EXTENDER.setForUnitTest(True)

# --------------------------------------------------------------------

from ally.container import ioc
from ally.core.http.impl.processor.method_invoker import MethodInvokerHandler
from ally.core.impl.node import NodeRoot
from ally.core.spec.resources import Invoker, Path
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context, create
from ally.design.processor.execution import Chain
from ally.design.processor.resolvers import resolversFor
from ally.http.spec.server import HTTP_GET
import unittest

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = defines(str)
    path = defines(Path)
    # ---------------------------------------------------------------- Defined
    invoker = defines(Invoker, doc='''
    @rtype: Invoker
    The invoker to be used for calling the service.
    ''')

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(str)
    status = defines(int)
    isSuccess = defines(bool)
    allows = defines(set, doc='''
    @rtype: set[string]
    Contains the allow list for the methods.
    ''')
ctx = create(resolversFor(contexts=dict(Request=Request, Response=Response)))
Request, Response = ctx['Request'], ctx['Response']

# --------------------------------------------------------------------

class TestMethodInvoker(unittest.TestCase):

    def testMethodInvoker(self):
        handler = MethodInvokerHandler()
        ioc.initialize(handler)
        request, response = Request(), Response()
        
        node = NodeRoot()
        request.method, request.path = HTTP_GET, Path([], node)

        Chain(handler.process, False, request=request, response=response).execute()

        self.assertEqual(response.allows, set())
        self.assertTrue(response.isSuccess is False)

# --------------------------------------------------------------------

if __name__ == '__main__': unittest.main()
