'''
Created on Sep 14, 2012

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the Babel conversion processor.
'''

from ..ally_core.processor import converterRequest, converterResponse, \
    default_language
from ..ally_core_http.processor import assemblyResources, \
    updateAssemblyResources
from ..ally_http.processor import contentTypeResponseEncode
from .processor import headersCustom
from ally.container import ioc
from ally.design.processor.handler import Handler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: import babel  # @UnusedImport
except ImportError: log.info('No Babel library available, no Babel conversion')
else:
    from ally.core.http.impl.processor.text_conversion import \
    BabelConverterRequestHandler, BabelConverterResponseHandler, BabelConversionEncodeHandler, FORMAT, CONTENT_FORMAT
    
    # --------------------------------------------------------------------
    
    @ioc.config
    def present_formatting():
        '''
        If true will place on the response header the used formatting for conversion of data.
        '''
        return True
    
    # --------------------------------------------------------------------

    @ioc.replace(converterRequest)
    def converterRequestBabel() -> Handler:
        b = BabelConverterRequestHandler()
        b.languageDefault = default_language()
        return b

    @ioc.replace(converterResponse)
    def converterResponseBabel() -> Handler:
        b = BabelConverterResponseHandler()
        b.languageDefault = default_language()
        return b
 
    @ioc.entity
    def babelConversionEncode() -> Handler: return BabelConversionEncodeHandler()
    
    # --------------------------------------------------------------------
    
    @ioc.before(headersCustom)
    def updateHeadersCustomForBabel():
        headersCustom().update(header.name for header in FORMAT.values())
        headersCustom().update(header.name for header in CONTENT_FORMAT.values())
    
    @ioc.after(updateAssemblyResources)
    def updateAssemblyResourcesForBabel():
        if present_formatting(): assemblyResources().add(babelConversionEncode(), after=contentTypeResponseEncode())
