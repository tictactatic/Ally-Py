'''
Created on Mar 26, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the structures object.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Path
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from ally.http.spec.server import IEncoderPath
from assemblage.api.assemblage import Structure
                    
# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    result = defines(object, doc='''
    @rtype: Structure
    The created structure.
    ''')
    # ---------------------------------------------------------------- Required
    structureId = requires(int)
    method = requires(str)
    required = requires(object)
    
class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(Path)
    encoderPath = requires(IEncoderPath)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideStructure')
class ProvideStructure(HandlerProcessor):
    '''
    Provides the structure object.
    '''
        
    def process(self, chain, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the strucure object.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        if obtain.required == Structure:
            assert obtain.structureId, 'A structure id is required'
            assert isinstance(support.encoderPath, IEncoderPath), 'Invalid encoder path %s' % support.encoderPath
            
            structure = Structure()
            structure.Id = obtain.structureId
            if obtain.method:
                assert isinstance(support.path, Path), 'Invalid path %s' % support.path
                structure.Method = obtain.method
                structure.Pattern = support.encoderPath.encodePattern(support.path, invalid=self.replace, quoted=False)
            obtain.result = structure
            return
        
        chain.proceed()
        
    # ----------------------------------------------------------------
    
    def replace(self, match, converterPath):
        '''
        Method used for replacing within the pattern path.
        '''
        return '[^\\/]+'
