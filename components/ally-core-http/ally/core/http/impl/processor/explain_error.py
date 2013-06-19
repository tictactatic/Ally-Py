'''
Created on Jun 28, 2011

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Provides support for explaining the errors in the content of the request.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, optional, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util import TextTable
from ally.support.util_io import IInputStream
from codecs import getwriter
from io import BytesIO
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    type = requires(Type)
    enumeration = requires(list)
    isOptional = requires(bool)
    description = requires(list)
    definitions = requires(set)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Optional
    errorMessage = optional(str, doc='''
    @rtype: string
    The error message for the error.
    ''')
    errorDefinition = optional(Context, doc='''
    @rtype: Context
    The definition that reflects the error.
    ''')
    # ---------------------------------------------------------------- Required
    status = requires(int)
    text = requires(str)
    code = requires(str)
    isSuccess = requires(bool)

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
class ExplainErrorHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides on the response a form of the error that can be extracted from 
    the response code and error message, this processor uses the code status (success) in order to trigger the error
    response.
    '''
    
    charSet = 'ASCII'
    # The content encoding to use for response.
    type = 'text/plain'
    # The content type for the reported error.
    
    def __init__(self):
        assert isinstance(self.charSet, str), 'Invalid character set encoding %s' % self.charSet
        assert isinstance(self.type, str), 'Invalid content type %s' % self.type
        super().__init__(Definition=Definition)

    def process(self, chain, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the error into a response content.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        if response.isSuccess is False:
            responseCnt.source = BytesIO()
            out = getwriter(self.charSet)(responseCnt.source)
            w = out.write
            
            w('Status: %s' % response.status)
            if response.text:
                w(' %s' % response.text)
                if response.code: w(' | %s' % response.code)
            elif response.code: w(' %s' % response.code)
            w('\n')
                
            if Response.errorMessage in response and response.errorMessage:
                w('%s\n' % response.errorMessage)
            
            if Response.errorDefinition in response and response.errorDefinition:
                definition = response.errorDefinition
                assert isinstance(definition, Definition), 'Invalid definition %s' % definition
                
                w('\n')
                if definition.description:
                    w('\n'.join(definition.description))
                    w('\n')
                
                if definition.definitions:
                    table = TextTable('Name', 'Type', 'Optional', 'Description')
                    
                    definitions = list(definition.definitions)
                    definitions.reverse()
                    definitions.sort(key=lambda definition: definition.name or '')
                    while definitions:
                        definition = definitions.pop()
                        assert isinstance(definition, Definition), 'Invalid definition %s' % definition
                        
                        if definition.definitions:
                            if definition.description: table.add('\n'.join(definition.description))
                            
                            sdefinitions = list(definition.definitions)
                            sdefinitions.reverse()
                            sdefinitions.sort(key=lambda definition: definition.name or '')
                            definitions.extend(sdefinitions)
                        elif definition.name:
                            if definition.enumeration:
                                represent = '\n'.join('- %s' % enum for enum in definition.enumeration)
                            elif definition.type: represent = str(definition.type)
                            else: represent = ''
                            table.add(definition.name, represent,
                                      '*' if definition.isOptional else '',
                                      '\n'.join(definition.description) if definition.description else '')
                    table.render(out)
            
            responseCnt.length = responseCnt.source.tell()
            responseCnt.source.seek(0)
            
            responseCnt.charSet = self.charSet
            responseCnt.type = self.type
