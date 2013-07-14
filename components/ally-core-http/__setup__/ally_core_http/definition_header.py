'''
Created on Jul 14, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the headers definitions.
'''

from ..ally_core.definition import addDescriber, definitionError, addError, \
    definitionDescribers, definitions, addDefinition
from ..ally_core.parsing_rendering import content_types_xml, content_types_json
from .processor import parametersAsHeaders, read_from_params
from ally.api.type import typeFor
from ally.container import ioc
from ally.core.http.spec.codes import PARAMETER_ILLEGAL, TIME_ZONE_ERROR
from ally.core.http.spec.transform.encdec import CATEGORY_HEADER
from ally.core.impl.verifier import VerifyName
from ally.core.spec.codes import ENCODING_UNKNOWN
from ally.http.spec.headers import ACCEPT, CONTENT_TYPE

# --------------------------------------------------------------------

INFO_TZ_DEFAULT = 'time_zone_default'
# The index for time zone default info.
INFO_TZ_SAMPLE = 'time_zone_sample'
# The index for time zone sample info.

VERIFY_ACCEPT = VerifyName(ACCEPT.name, category=CATEGORY_HEADER)
VERIFY_CONTENT_TYPE = VerifyName(CONTENT_TYPE.name, category=CATEGORY_HEADER)

# --------------------------------------------------------------------

@ioc.entity
def headerParamVerifiers():
    return [VerifyName(name, category=CATEGORY_HEADER) for name in parametersAsHeaders()]

# --------------------------------------------------------------------

@ioc.before(definitions)
def updateDefinitionsForHeaders():
    values = set(content_types_json())
    values.update(content_types_xml())
    values.discard(None)
    
    addDefinition(category=CATEGORY_HEADER,
                  name=ACCEPT.name,
                  type=typeFor(str),
                  enumeration=list(values),
                  isOptional=True)
    
    addDefinition(category=CATEGORY_HEADER,
                  name=CONTENT_TYPE.name,
                  type=typeFor(str),
                  isOptional=True)
        
@ioc.before(definitionError)
def updateDefinitionErrorForHeaders():
    addError(ENCODING_UNKNOWN.code, VERIFY_ACCEPT, VERIFY_CONTENT_TYPE)
    if read_from_params():
        addError(PARAMETER_ILLEGAL.code, *headerParamVerifiers())
    
@ioc.before(definitionDescribers)
def updateDescribersForHeaders():
    addDescriber(VERIFY_ACCEPT,
                 'the accepted encodings, based on http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html',
                 'the simple mime types (the ones with no slash) can be provided as URL extension')
    addDescriber(VERIFY_CONTENT_TYPE,
                 'same as \'' + ACCEPT.name + '\' header but is to provide the input content encoding')
    
    if read_from_params():
        for verifier in headerParamVerifiers(): addDescriber(verifier, 'the header value can also be provided as a parameter')

# --------------------------------------------------------------------

try: import pytz  # @UnusedImport
except ImportError: pass
else:
    from pytz import all_timezones
    from ally.core.http.impl.processor.time_zone import TIME_ZONE, CONTENT_TIME_ZONE
    from .processor_time_zone import default_time_zone

    # --------------------------------------------------------------------
    
    VERIFY_TIME_ZONE = VerifyName(TIME_ZONE.name, category=CATEGORY_HEADER)
    VERIFY_CONTENT_TIME_ZONE = VerifyName(CONTENT_TIME_ZONE.name, category=CATEGORY_HEADER)

    # --------------------------------------------------------------------
    
    @ioc.before(definitions)
    def updateDefinitionsForTimeZone():
        sample, curr = [], None
        for tz in all_timezones:
            if curr != tz[:1]:
                sample.append(tz)
                curr = tz[:1]
        
        addDefinition(category=CATEGORY_HEADER,
                      name=TIME_ZONE.name,
                      type=typeFor(str),
                      isOptional=True,
                      info={INFO_TZ_SAMPLE: sample, INFO_TZ_DEFAULT: default_time_zone()})
        
        addDefinition(category=CATEGORY_HEADER,
                      name=CONTENT_TIME_ZONE.name,
                      type=typeFor(str),
                      isOptional=True,
                      info={INFO_TZ_SAMPLE: sample, INFO_TZ_DEFAULT: default_time_zone()})
        
    @ioc.before(definitionError)
    def updateDefinitionErrorForTimeZone():
        addError(TIME_ZONE_ERROR.code, VERIFY_TIME_ZONE, VERIFY_CONTENT_TIME_ZONE)
        
    @ioc.before(updateDescribersForHeaders)
    def updateDescribersForTimeZone():
        # This is based on @see: updateDefinitionsForTimeZone().
        addDescriber(VerifyName(TIME_ZONE.name, category=CATEGORY_HEADER),
                     'the time zone to render the time stamps in, as an example:\n%(' + INFO_TZ_SAMPLE + ')s',
                     'the default time zone is %(' + INFO_TZ_DEFAULT + ')s')
        addDescriber(VerifyName(CONTENT_TIME_ZONE.name, category=CATEGORY_HEADER),
                     'the same as \'' + TIME_ZONE.name + '\' but for parsed content')
