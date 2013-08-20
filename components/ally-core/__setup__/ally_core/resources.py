'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the resources.
'''

from .decode import assemblyDecode, assemblyDecodeExport, \
    updateAssemblyDecodeExport
from .definition import definitions
from .encode import assemblyEncode
from ally.container import ioc
from ally.container.priority import PRIORITY_LOAD_ENTITIES
from ally.core.impl.processor.assembler.decoding import DecodingHandler, \
    decodingExport
from ally.core.impl.processor.assembler.definition import DefinitionHandler
from ally.core.impl.processor.assembler.encoding import EncodingHandler
from ally.core.impl.processor.assembler.injector_assembly import \
    InjectorAssemblyHandler
from ally.core.impl.processor.assembler.invoker_service import \
    InvokerServiceHandler
from ally.core.impl.processor.assembler.process_method import \
    ProcessMethodHandler
from ally.core.impl.processor.assembler.validate_hints import \
    ValidateHintsHandler
from ally.core.impl.processor.assembler.validate_solved import \
    ValidateSolvedHandler
from ally.core.impl.processor.content import AssemblerContentHandler
from ally.design.priority import Priority
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

PRIORITY_REGISTER = Priority('Register services', after=PRIORITY_LOAD_ENTITIES)
# The register priority.

# --------------------------------------------------------------------

@ioc.entity
def assemblyAssembler() -> Assembly:
    '''
    The assembly containing the handlers to be used in the assembly of invokers into the root node.
    '''
    return Assembly('Assemblers')

# --------------------------------------------------------------------

@ioc.entity
def services() -> list:
    ''' The list of services to be registered'''
    return []

@ioc.entity
def injectorAssembly() -> Handler:
    b = InjectorAssemblyHandler()
    b.assembly = assemblyAssembler()
    return b

@ioc.entity
def invokerService() -> Handler: return InvokerServiceHandler()

@ioc.entity
def processMethod() -> Handler: return ProcessMethodHandler()

@ioc.entity
def decoding() -> Handler:
    b = DecodingHandler()
    b.decodeAssembly = assemblyDecode()
    return b

@ioc.entity
def encoding() -> Handler:
    b = EncodingHandler()
    b.encodeAssembly = assemblyEncode()
    return b

@ioc.entity
def assemblerContent() -> Handler: return AssemblerContentHandler()

@ioc.entity
def validateSolved() -> Handler: return ValidateSolvedHandler()

@ioc.entity
def validateHints() -> Handler: return ValidateHintsHandler()

@ioc.entity
def definition() -> Handler:
    b = DefinitionHandler()
    b.definitions = definitions()
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyAssembler)
def updateAssemblyAssembler():
    assemblyAssembler().add(invokerService(), processMethod(), decoding(), encoding(), assemblerContent(),
                            validateSolved(), validateHints(), definition())

@ioc.after(updateAssemblyDecodeExport)
def updateAssemblyDecodeExportForDecoding():
    assemblyDecodeExport().add(decodingExport)
    
# --------------------------------------------------------------------

@ioc.start(priority=PRIORITY_REGISTER)
def register():
    log.info('Registering %s services into the resources structure', len(services()))
    injectorAssembly().registerServices(services())
    
