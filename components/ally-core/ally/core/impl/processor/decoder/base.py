'''
Created on Aug 5, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.design.processor.resolvers import resolverFor, resolversFor, solve
from ally.design.processor.spec import IResolver
from collections import Iterable
from ally.design.processor.assembly import Assembly
from ally.design.processor.execution import Processing

# --------------------------------------------------------------------

class FailureTarget(Context):
    '''
    The target failure context.
    '''
    # ---------------------------------------------------------------- Required
    failures = defines(list, doc='''
    @rtype: list[tuple(Context, object, list[string], dictionary{string: object})]
    Contains the decode failures as a list containing tuples having on the first position the decoding context that
    reported the failure, on the second position the value that have failed decoding, on the third position the messages
    associated with the failure and on the last position the data used for messages place holders.
    ''')
      
# --------------------------------------------------------------------

def addFailure(target, decoding, *messages, value=None, **data):
    '''
    Adds a new failure entry.
    
    @param target: Context
        The target context to add the failure to.
    @param decoding: Context
        The decoding context to add the failure to.
    @param messages: arguments[string|Iterable(string)]
        The failure messages to add.
    @param value: object
        The value that is the failure target.
    @param data: key arguments
        Data to be used for messages place holders.
    '''
    assert isinstance(target, FailureTarget), 'Invalid target context %s' % target
    assert isinstance(decoding, Context), 'Invalid context %s' % decoding
    msgs = []
    for message in messages:
        if isinstance(message, str): msgs.append(message)
        else:
            assert isinstance(message, Iterable), 'Invalid message %s' % message
            for msg in message:
                assert isinstance(msg, str), 'Invalid message %s' % msg
                msgs.append(msg)
    
    if target.failures is None: target.failures = []
    target.failures.append((decoding, value, msgs, data))

# --------------------------------------------------------------------

class DefineExport(Context):
    '''
    The define export context.
    '''
    # ---------------------------------------------------------------- Required
    Target = defines(IResolver, doc='''
    @rtype: IResolver
    The target resolver.
    ''')
    arg = defines(dict, doc='''
    @rtype: dictionary{string: IResolver}
    The context resolvers for target arguments.
    ''')
    
class RequestExport(Context):
    '''
    The request export context.
    '''
    # ---------------------------------------------------------------- Required
    Target = requires(IResolver)
    arg = requires(dict)

class ExportingTarget(HandlerProcessor):
    '''
    Implementation for a handler that provides the target exporting.
    '''
    
    def __init__(self, Target, **arg):
        super().__init__()
        self.Target = resolverFor(Target)
        self.arg = resolversFor(arg)
        
    def process(self, chain, export:DefineExport, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the export.
        '''
        assert isinstance(export, DefineExport), 'Invalid export %s' % export
        
        if export.Target:
            assert isinstance(export.Target, IResolver), 'Invalid target %s' % export.Target
            export.Target = export.Target.solve(self.Target)
        else: export.Target = self.Target
        
        if export.arg is None: export.arg = {}
        solve(export.arg, self.arg)

def importTarget(exportAssembly):
    '''
    Imports the target context.
    
    @param exportAssembly: Assembly
        The assembly containing the exported targets.
    @return: tuple(IResolver, dictionary{string: IResolver})
        The target resolver and the target arguments resolvers.
    '''
    assert isinstance(exportAssembly, Assembly), 'Invalid export assembly %s' % exportAssembly
    processing = exportAssembly.create(export=RequestExport)
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    arg = processing.executeWithAll()
    assert isinstance(arg.export, RequestExport), 'Invalid export %s' % arg.export
    assert isinstance(arg.export.Target, IResolver), 'Invalid resolver %s' % arg.export.Target
    return arg.export.Target, arg.export.arg

failureTargetExport = ExportingTarget(FailureTarget)
# The target failure export.
