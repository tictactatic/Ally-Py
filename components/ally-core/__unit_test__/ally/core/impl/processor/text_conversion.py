'''
Created on Jun 21, 2012

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Text conversion testing.
'''

# Required in order to register the package extender whenever the unit test is run.
if True:
    import package_extender
    package_extender.PACKAGE_EXTENDER.setForUnitTest(True)

# --------------------------------------------------------------------

from ally.container import ioc
from ally.core.impl.processor.text_conversion import ConverterResponseHandler, \
    ConverterRequestHandler
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context, create
from ally.design.processor.execution import Chain
from ally.design.processor.resolvers import resolversFor
import unittest

# --------------------------------------------------------------------

class Content(Context):
    converter = defines(Converter)
ctx = create(resolversFor(contexts=dict(Content=Content)))
Content = ctx['Content']

# --------------------------------------------------------------------

class TestTextConversion(unittest.TestCase):

    def testTextConversion(self):
        handlers = []
        converter = Converter()
        
        handler = ConverterRequestHandler()
        handler.converter = converter
        ioc.initialize(handler)
        handlers.append(handler)
        
        handler = ConverterResponseHandler()
        handler.converter = converter
        ioc.initialize(handler)
        handlers.append(handler)

        request, response = Content(), Content()
        def callProcess(chain, **keyargs):
            for handler in handlers: handler.process(chain, **keyargs)
        Chain(callProcess, False, request=request, response=response).execute()

        self.assertEqual(converter, response.converter)
        self.assertEqual(converter, request.converter)


# --------------------------------------------------------------------

if __name__ == '__main__': unittest.main()
