'''
Created on Jun 28, 2011

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Provides support for explaining the errors in the content of the request.
'''

from ally.container.ioc import injected
from ally.core.spec.definition import IValue, IVerifier
from ally.design.processor.attribute import requires, optional, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.design.processor.resolvers import resolversFor
from ally.support.util import TextTable
from ally.support.util_io import IInputStream
from codecs import getwriter
from collections import deque
from io import BytesIO
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------
  
class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Optional
    isMandatory = optional(bool)
    enumeration = optional(list)
    references = optional(list)
    # ---------------------------------------------------------------- Required
    name = requires(str)
    types = requires(list)
    
class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    code = requires(str)
    isSuccess = requires(bool)
    status = requires(int)
    text = requires(str)
    errors = requires(list)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Optional
    source = defines(IInputStream)
    type = defines(str)
    charSet = defines(str)
    length = defines(int)
      
# --------------------------------------------------------------------

@injected
class ErrorExplainHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides on the response a form of the error that can be extracted from 
    the response code and error message, this processor uses the code status (success) in order to trigger the error
    response.
    '''
    
    descriptions = list
    # The descriptions (list[tuple(IVerifier, tuple(string), dictionary{string: object})]) used in constructing the error.
    charSet = 'ASCII'
    # The content encoding to use for response.
    type = 'text/plain'
    # The content type for the reported error.
    
    def __init__(self):
        assert isinstance(self.descriptions, list), 'Invalid descriptions %s' % self.descriptions
        assert isinstance(self.charSet, str), 'Invalid character set encoding %s' % self.charSet
        assert isinstance(self.type, str), 'Invalid content type %s' % self.type
        
        resolvers = resolversFor(dict(Definition=Definition))
        for verifier, descriptions, data in self.descriptions:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            assert isinstance(descriptions, tuple), 'Invalid descriptions %s' % descriptions
            assert isinstance(data, dict), 'Invalid data %s' % data
            if __debug__:
                for desc in descriptions: assert isinstance(desc, str), 'Invalid description %s' % desc
                
            verifier.prepare(resolvers)
                
            for value in data.values():
                if isinstance(value, IValue):
                    assert isinstance(value, IValue)
                    value.prepare(resolvers)
        
        super().__init__(**resolvers)

    def process(self, chain, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the error into a response content.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        if response.isSuccess is not False: return  # Not in error.
        
        responseCnt.source = BytesIO()
        out = getwriter(self.charSet)(responseCnt.source)
        w = out.write
        
        w('Status: %s' % response.status)
        if response.text:
            w(' %s' % response.text)
            if response.code: w(' | %s' % response.code)
        elif response.code: w(' %s' % response.code)
        w('\n')
        
        if response.errors:
            for messages, data, contexts in response.errors:
                data = self.transformData(data)
                w('\n')
                w('\n'.join(msg % data for msg in messages))
                if contexts:
                    w('\n')
                    self.render(out, contexts)
                else: w('\n')
        
        responseCnt.length = responseCnt.source.tell()
        responseCnt.source.seek(0)
        
        responseCnt.charSet = self.charSet
        responseCnt.type = self.type

    # ----------------------------------------------------------------
    
    def render(self, out, contexts):
        '''
        Renders the definition contexts to the provided output stream.
        '''
        table = TextTable('*', 'Name', 'Type', 'Description')
        presented, stack = set(), deque()
        stack.extend(contexts)
        while stack:
            defin = stack.popleft()
            assert isinstance(defin, Definition), 'Invalid definition %s' % defin
            
            if Definition.references in defin and defin.references:
                stack.extendleft(defin.references)
            
            if defin.name and defin.name not in presented:
                presented.add(defin.name)
                
                if Definition.enumeration in defin and defin.enumeration:
                    represent = '\n'.join('- %s' % enum for enum in defin.enumeration)
                elif defin.types: represent = ', '.join(str(typ) for typ in defin.types)
                else: represent = ''
                
                mandatory = ''
                if Definition.isMandatory in defin and defin.isMandatory: mandatory = '*'
                
                table.add(mandatory, defin.name, represent, self.descriptionFor(defin))
                    
        if presented: table.render(out)
    
    def transformData(self, data, definition=None):
        '''
        Transforms the data dictionary to proper values.
        '''
        assert isinstance(data, dict), 'Invalid data %s' % data
        
        tansformed = {}
        for key, value in data.items():
            if isinstance(value, IValue):
                assert isinstance(value, IValue)
                value = value.get(definition)
                
            if value is not None:
                if isinstance(value, list): tansformed[key] = '\n%s\n' % '\n'.join(str(item) for item in value)
                else: tansformed[key] = str(value)
            
        return tansformed
    
    def descriptionFor(self, definition):
        '''
        Construct the description for the provided definition.
        '''
        assert isinstance(definition, Definition), 'Invalid definition %s' % definition
        
        compiled = []
        for verifier, descriptions, data in self.descriptions:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            if verifier.isValid(definition):
                data = self.transformData(data, definition)
                for description in descriptions:
                    try: compiled.append(description % data)
                    except KeyError: raise Exception('Description \'%s\' could not be completed' % description)
        
        return '\n'.join(compiled)
        
