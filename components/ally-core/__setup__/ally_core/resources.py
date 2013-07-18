'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the resources.
'''

from .definition import definitions
from .encode import assemblyEncode
from ally.container import ioc
from ally.core.impl.processor.assembler.definition import DefinitionHandler
from ally.core.impl.processor.assembler.encoding import EncodingHandler
from ally.core.impl.processor.assembler.injector_assembly import \
    InjectorAssemblyHandler
from ally.core.impl.processor.assembler.invoker_service import \
    InvokerServiceHandler
from ally.core.impl.processor.assembler.option_slice import OptionSliceHandler
from ally.core.impl.processor.assembler.process_method import \
    ProcessMethodHandler
from ally.core.impl.processor.assembler.validate_hints import \
    ValidateHintsHandler
from ally.core.impl.processor.assembler.validate_solved import \
    ValidateSolvedHandler
from ally.core.impl.processor.content import AssemblerContentHandler
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.config
def slice_limit_maximum() -> int:
    ''' The maximum imposed slice limit on a collection, if none then no maximum limit will be imposed'''
    return 100

@ioc.config
def slice_limit_default() -> int:
    '''
    The default slice limit on a collection if none is specified, if none then the 'slice_limit_maximum' limit
    will be used as the default one.
    '''
    return 30

@ioc.config
def slice_with_total() -> bool:
    ''' The default value for providing the total count'''
    return True

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
def optionSlice() -> Handler:
    b = OptionSliceHandler()
    b.maximumLimit = slice_limit_maximum()
    b.defaultLimit = slice_limit_default()
    b.defaultWithTotal = slice_with_total()
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

@ioc.entity
def assemblyAssembler() -> Assembly:
    '''
    The assembly containing the handlers to be used in the assembly of invokers into the root node.
    '''
    return Assembly('Assemblers')

# --------------------------------------------------------------------

@ioc.before(assemblyAssembler)
def updateAssemblyAssembler():
    assemblyAssembler().add(invokerService(), processMethod(), encoding(), optionSlice(), assemblerContent(),
                            validateSolved(), validateHints(), definition())

# --------------------------------------------------------------------

@ioc.start(priority=ioc.PRIORITY_FINAL)
def register():
    log.info('Registering %s services into the resources structure', len(services()))
    injectorAssembly().registerServices(services())
    
