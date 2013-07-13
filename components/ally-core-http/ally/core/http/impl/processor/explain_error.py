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
from ally.core.spec.transform.describer import IVerifier
from ally.core.spec.transform.encdec import Category
from ally.design.processor.attribute import requires, optional, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.design.processor.resolvers import resolversFor
from ally.support.util import TextTable
from ally.support.util_io import IInputStream
from codecs import getwriter
from io import BytesIO
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Optional
    info = optional(dict)

class Solicitation(Context):
    '''
    The decoder solicitation context.
    '''
    # ---------------------------------------------------------------- Optional
    info = optional(dict)
    solicitation = optional(Context)
    invoker = optional(Context)
  
class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Optional
    info = optional(dict)
    solicitation = optional(Context)
    enumeration = optional(list)
    # ---------------------------------------------------------------- Required
    name = requires(str)
    category = requires(Category)
    type = requires(Type)
    isOptional = requires(bool)
    
class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Optional
    errorMessages = optional(list, doc='''
    @rtype: list[string]
    The error messages.
    ''')
    errorDefinitions = optional(list, doc='''
    @rtype: list[Context]
    The definitions that reflects the error.
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
    
    describers = list
    # The describers (list[tuple(ITrigger, string)]) used in constructing the error.
    charSet = 'ASCII'
    # The content encoding to use for response.
    type = 'text/plain'
    # The content type for the reported error.
    
    def __init__(self):
        assert isinstance(self.describers, list), 'Invalid describers %s' % self.describers
        assert isinstance(self.charSet, str), 'Invalid character set encoding %s' % self.charSet
        assert isinstance(self.type, str), 'Invalid content type %s' % self.type
        
        resolvers = resolversFor(dict(Invoker=Invoker, Solicitation=Solicitation, Definition=Definition))
        for verifier, *descriptions in self.describers:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            if __debug__:
                for description in descriptions:
                    assert isinstance(description, str), 'Invalid description %s' % description
            verifier.prepare(resolvers)
        
        super().__init__(**resolvers)

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
                
            if Response.errorMessages in response and response.errorMessages:
                w('%s\n' % '\n'.join(response.errorMessages))
            
            if Response.errorDefinitions in response and response.errorDefinitions:
                w('\n')
                table, header = None, None
                for defin in response.errorDefinitions:
                    assert isinstance(defin, Definition), 'Invalid definition %s' % defin

                    if Definition.enumeration in defin and defin.enumeration:
                        represent = '\n'.join('- %s' % enum for enum in defin.enumeration)
                    elif defin.type: represent = str(defin.type)
                    else: represent = ''
                    
                    if header:
                        if defin.category != header.category:
                            table.render(out)
                            table = None

                    if table is None:
                        if defin.category:
                            assert isinstance(defin.category, Category), 'Invalid category %s' % defin.category
                            if defin.category.info:
                                w('\n'.join(defin.category.info))
                                w('\n')
                            
                        table = TextTable('Name', 'Type', 'Optional', 'Description')
                        header = defin
                    
                    table.add(defin.name, represent, '*' if defin.isOptional else '', self.descriptionFor(defin))
                    
                if table: table.render(out)
            
            responseCnt.length = responseCnt.source.tell()
            responseCnt.source.seek(0)
            
            responseCnt.charSet = self.charSet
            responseCnt.type = self.type

    # ----------------------------------------------------------------
    
    def descriptionFor(self, definition):
        '''
        Construct the description for the provided definition.
        '''
        assert isinstance(definition, Definition), 'Invalid definition %s' % definition
        
        info = {}
        if Definition.info in definition and definition.info: info.update(definition.info)
        if Definition.solicitation in definition and definition.solicitation:
            solicitation = definition.solicitation
            assert isinstance(solicitation, Solicitation), 'Invalid solicitation %s' % solicitation
            
            while solicitation:
                if Solicitation.info in solicitation and solicitation.info: info.update(solicitation.info)
                if Solicitation.invoker in solicitation and solicitation.invoker:
                    if Invoker.info in solicitation.invoker:
                        assert isinstance(solicitation.invoker, Invoker), 'Invalid invoker %s' % solicitation.invoker
                        if solicitation.invoker.info: info.update(solicitation.invoker.info)
                        
                if Solicitation.solicitation in solicitation: solicitation = solicitation.solicitation
                else: solicitation = None
        
        keys = set(info.keys())
        for key in keys:
            value = info.get(key)
            if isinstance(value, (list, tuple)): info[key] = ', '.join(value)

        compiled = []
        for verifier, *descriptions in self.describers:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            for description in descriptions:
                assert isinstance(description, str), 'Invalid description %s' % description
                if verifier.isValid(definition, keys): compiled.append(description % info)
        
        return '\n'.join(compiled)
        
