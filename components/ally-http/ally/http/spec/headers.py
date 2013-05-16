'''
Created on Apr 30, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP headers support.
'''

from ally.design.processor.attribute import defines, optional
from ally.design.processor.context import Context
from collections import Iterable
import re

# --------------------------------------------------------------------

SEPARATOR_MAIN = ','
# The separator used in splitting value and attributes from each other. 
SEPARATOR_ATTR = ';'
# The separator used between the attributes and value.
SEPARATOR_VALUE = '='
# The separator used between attribute name and attribute value.

# --------------------------------------------------------------------

class HeadersRequire(Context):
    '''
    Context for required headers. 
    '''
    # ---------------------------------------------------------------- Required
    headers = optional(dict, doc='''
    @rtype: dictionary{string, string}
    The raw headers.
    ''')
    
class HeadersDefines(Context):
    '''
    Context for defined headers. 
    '''
    # ---------------------------------------------------------------- Defined
    headers = defines(dict, doc='''
    @rtype: dictionary{string, string}
    The raw headers.
    ''')

# --------------------------------------------------------------------

class Header:
    '''
    Simple header container.
    '''
    __slots__ = ('name', 'nameLower')
    
    def __init__(self, name):
        '''
        Construct a simple header.
        
        @param name: string
            The header name.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        self.name = name
        self.nameLower = name.lower()
        
    def has(self, headers):
        '''
        Checks if the header (case insensitive) is present in headers.
        
        @param headers: Context|dictionary{string: string}
            The headers to check for the header.
        @return: boolean
            True if the header is present, False otherwise.
        '''
        if isinstance(headers, Context):
            if HeadersRequire.headers not in headers or headers.headers is None: return False
            headers = headers.headers
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        for hname in headers.keys():
            assert isinstance(hname, str), 'Invalid header name %s' % hname
            if hname.lower() == self.nameLower: return True
        return False
        
    def remove(self, headers):
        '''
        Removes the header (case insensitive).
        
        @param headers: Context|dictionary{string: string}
            The headers to set the value to.
        '''
        if isinstance(headers, Context):
            if HeadersRequire.headers not in headers or headers.headers is None: return
            headers = headers.headers
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        for hname in list(headers.keys()):
            assert isinstance(hname, str), 'Invalid header name %s' % hname
            if hname.lower() == self.nameLower: headers.pop(hname)

class HeaderRaw(Header):
    '''
    Simple raw header operator.
    '''
    __slots__ = ()
    
    def __init__(self, name):
        '''
        Construct a simple raw header.
        @see: Header.__init__
        '''
        super().__init__(name)
        
    def fetch(self, headers):
        '''
        Get the raw header value, if multiple headers are found with the same name (case insensitive)
        then the returned values will be the first header value.
        
        @param headers: Context|dictionary{string: string}
            The headers to get the value from.
        @return: string|None
            The raw header value or None if there is no such header.
        '''
        if isinstance(headers, Context):
            if HeadersRequire.headers not in headers or headers.headers is None: return
            headers = headers.headers
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        for hname, hvalue in headers.items():
            assert isinstance(hname, str), 'Invalid header name %s' % hname
            if hname.lower() == self.nameLower: return hvalue
            
    def fetchOnce(self, headers):
        '''
        Get the raw header value, if multiple headers are found with the same name (case insensitive)
        then the returned values will be the first header value.
        Removes the header (case insensitive).
        
        @param headers: Context|dictionary{string: string}
            The headers to set the value to.
        @return: string|None
            The raw header value or None if there is no such header.
        '''
        value = self.fetch(headers)
        self.remove(headers)
        return value
    
    def put(self, headers, value):
        '''
        Puts the raw header value into the headers.
        
         @param headers: Context|dictionary{string: string}
            The headers to put the value to.
        @param value: string
            The value to put for the header.
        '''
        if isinstance(headers, HeadersDefines):
            if headers.headers is None: headers.headers = {}
            headers = headers.headers
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        assert isinstance(value, str), 'Invalid value %s' % value
        self.remove(headers)
        headers[self.name] = value

class HeaderCmx(Header):
    '''
    Multiple values header complex operator.
    '''
    __slots__ = ('withAttributes', 'sepMain', 'sepAttr', 'sepValue', '_rexMain', '_rexAttr', '_rexValue')
    
    def __init__(self, name, withAttributes,
                 sepMain=SEPARATOR_MAIN, sepAttr=SEPARATOR_ATTR, sepValue=SEPARATOR_VALUE):
        '''
        Construct a multiple values complex header.
        @see: Header.__init__
        
        @param withAttributes: boolean
            Flag indicating that also the attributes should be fetched.
        @param sepMain: string
            The separator used in splitting value and attributes from each other.
        @param sepAttr: string
            The separator used between the attributes and value.
        @param sepValue: string
            The separator used between attribute name and attribute value.
        '''
        assert isinstance(withAttributes, bool), 'Invalid with attributes flag %s' % withAttributes
        assert isinstance(sepMain, str), 'Invalid separator main %s' % sepMain
        assert isinstance(sepAttr, str), 'Invalid separator attributes %s' % sepAttr
        assert isinstance(sepValue, str), 'Invalid separator values %s' % sepValue
        super().__init__(name)
        
        self.withAttributes = withAttributes
        self.sepMain = sepMain
        self.sepAttr = sepAttr
        self.sepValue = sepValue
        
        self._rexMain = re.compile(sepMain)
        self._rexAttr = re.compile(sepAttr)
        self._rexValue = re.compile(sepValue)

    def decode(self, headers):
        '''
        Get the decoded header values, if multiple headers are found with the same name (case insensitive)
        then the returned values will be composed of all headers values.
        
        @param headers: Context|dictionary{string: string}
            The headers to decode the value from.
        @return: list[string]|list[tuple(string, dictionary{string:string})]
            A list of tuples having as the first entry the header value and the second entry a dictionary 
            with the value attribute if attributes are requested, otherwise just a list with the values.
        '''
        if isinstance(headers, Context):
            if HeadersRequire.headers not in headers or headers.headers is None: return
            headers = headers.headers
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        
        parsed = []
        for hname, hvalue in headers.items():
            assert isinstance(hname, str), 'Invalid header name %s' % hname
            if hname.lower() != self.nameLower: continue
            for values in self._rexMain.split(hvalue):
                valAttr = self._rexAttr.split(values)
                if self.withAttributes:
                    attributes = {}
                    for k in range(1, len(valAttr)):
                        val = self._rexValue.split(valAttr[k])
                        attributes[val[0].strip()] = val[1].strip().strip('"') if len(val) > 1 else None
                    parsed.append((valAttr[0].strip(), attributes))
                else: parsed.append(valAttr[0].strip())
        return parsed
    
    def decodeOnce(self, headers):
        '''
        Get the decoded header values, if multiple headers are found with the same name (case insensitive)
        then the returned values will be composed of all headers values.
        Removes the header (case insensitive).
        
        @param headers: Context|dictionary{string: string}
            The headers to decode the value from.
        @return: list[string]|list[tuple(string, dictionary{string:string})]
            A list of tuples having as the first entry the header value and the second entry a dictionary 
            with the value attribute if attributes are requested, otherwise just a list with the values.
        '''
        value = self.decode(headers)
        self.remove(headers)
        return value
    
    def encode(self, headers, *value):
        '''
        Encode the header (case insensitive), with the values.
        ex:
            convert('multipart/formdata', 'mixed') == 'multipart/formdata, mixed'
            
            convert(('multipart/formdata', {'charset': 'utf-8', 'boundry': '12'})) ==
            'multipart/formdata; charset=utf-8; boundry=12'
        
        @param headers: Context|dictionary{string: string}
            The headers to place the value to.
        @param value: arguments[string|tuple(string, dictionary{string: string})]
            The value as arguments or if attributes are requested tuples containing as first value found in the header
            and as the second value a dictionary with the values attribute.
        '''
        if isinstance(headers, HeadersDefines):
            if headers.headers is None: headers.headers = {}
            headers = headers.headers
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        self.remove(headers)
        
        values = []
        for val in value:
            if isinstance(val, str): values.append(val)
            else:
                assert self.withAttributes, 'Invalid value %s' % (val,)
                assert isinstance(val, tuple), 'Invalid value %s' % val
                value, attributes = val
                assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
                attributes = self.sepAttr.join(self.sepValue.join(item) for item in attributes.items())
                values.append(self.sepAttr.join((value, attributes)) if attributes else value)
        headers[self.name] = self.sepMain.join(values)
        
    def extend(self, headers, *value):
        '''
        Extends the header(s) with the provided name (case insensitive), with the values.
        
        @param headers: Context|dictionary{string: string}
            The headers to place the value to.
        @param value: arguments[string|tuple(string, dictionary{string: string})]
            The value as arguments or if attributes are requested tuples containing as first value found in the header
            and as the second value a dictionary with the values attribute.
        '''
        values = self.decodeOnce(headers)
        if values: values.extend(value)
        else: values = value
        self.encode(headers, *values)
        
# --------------------------------------------------------------------

HOST = HeaderRaw('Host')
# Host as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.23
ACCEPT = HeaderCmx('Accept', False)
# Accept as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.1
ACCEPT_CHARSET = HeaderCmx('Accept-Charset', False)
# Accept charset as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.2
ALLOW = HeaderCmx('Allow', False)
# Allow as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.7
CONNECTION = HeaderRaw('Connection')
# Connection as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.10
CONTENT_TYPE = HeaderCmx('Content-Type', True)
# Content type as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.17
CONTENT_LENGTH = HeaderRaw('Content-Length')
# Content length as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.13
CONTENT_INDEX = HeaderRaw('Content-Index')
# The content index header.
TRANSFER_ENCODING = HeaderRaw('Transfer-Encoding')
# Transfer encoding as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.41

# Access control headers
ALLOW_ORIGIN = HeaderCmx('Access-Control-Allow-Origin', False)
# Allow origin as described at: http://www.w3.org/TR/cors/ chapter 5.1
ALLOW_METHODS = HeaderCmx('Access-Control-Allow-Methods', False)
# Allow methods as described at: http://www.w3.org/TR/cors/ chapter 5.5
ALLOW_HEADERS = HeaderCmx('Access-Control-Allow-Headers', False)
# Allow headers as described at: http://www.w3.org/TR/cors/ chapter 5.6
PARAMETERS_AS_HEADERS = HeaderCmx('Access-Control-Parameters-Headers', False)
# The header used for delivering the parameters that need to be interpreted as headers.

# --------------------------------------------------------------------

CONTENT_TYPE_ATTR_CHAR_SET = 'charset'
# The name of the CONTENT_TYPE attribute where the character set is provided.

# --------------------------------------------------------------------

CONNECTION_CLOSE = 'close'
# The value close to set on the CONNECTION header.
CONNECTION_KEEP = 'keep-alive'
# The value keep to set on the CONNECTION header.
TRANSFER_ENCODING_CHUNKED = 'chunked'
# The chunked value to place on the TRANSFER_ENCODING header.

# --------------------------------------------------------------------

def encode(headers, name, *value):
    '''
    Encode the header(s) with the provided name (case insensitive), with the values.

    @param headers: Context|dictionary{string: string}
        The headers to push the source to.
    @param name: string
        The name of the header to place.
    @param value: arguments[tuple(string, dictionary{string: string})|string]
        Tuples containing as first value found in the header and as the second value a dictionary with the
        values attribute.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    if isinstance(headers, HeadersDefines):
        if headers.headers is None: headers.headers = {}
        else:
            lname = name.lower()
            for hname in list(headers.headers.keys()):
                assert isinstance(hname, str), 'Invalid header name %s' % hname
                if hname.lower() == lname: headers.headers.pop(hname)
        headers = headers.headers
    assert isinstance(headers, dict), 'Invalid headers %s' % headers
    
    values = []
    for val in value:
        assert isinstance(val, Iterable), 'Invalid value %s' % val
        if isinstance(val, str): values.append(val)
        else:
            value, attributes = val
            assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
            attributes = SEPARATOR_ATTR.join(SEPARATOR_VALUE.join(item) for item in attributes.items())
            values.append(SEPARATOR_ATTR.join((value, attributes)) if attributes else value)
    headers[name] = SEPARATOR_MAIN.join(values)
    
def remove(headers, names):
    '''
    Removes the header (case insensitive).
    
    @param headers: Context|dictionary{string: string}
        The headers to set the value to.
    @param names: string|Iterable(string)
        The names to be removed.
    '''
    if isinstance(headers, Context):
        if HeadersRequire.headers not in headers or headers.headers is None: return
        headers = headers.headers
    assert isinstance(headers, dict), 'Invalid headers %s' % headers
    if isinstance(names, str): names = (names,)
    assert isinstance(names, Iterable), 'Invalid names %s' % names
    
    for name in names:
        assert isinstance(name, str), 'Invalid header name %s' % name
        name = name.lower()
        for hname in list(headers.keys()):
            assert isinstance(hname, str), 'Invalid header name %s' % hname
            if hname.lower() == name: headers.pop(hname)
