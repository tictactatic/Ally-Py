'''
Created on Mar 26, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblages.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.transform.render import IPattern
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from assemblage.api.assemblage import Assemblage
from collections import Iterable
import itertools

# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    result = defines(Iterable, doc='''
    @rtype: Iterable(Assemblage)
    The generated result assemblages.
    ''')
    # ---------------------------------------------------------------- Required
    assemblageId = requires(str)
    required = requires(object)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    pattern = defines(IPattern, doc='''
    @rtype: IPattern
    The pattern to be used in generating the matchers.
    ''')
    # ---------------------------------------------------------------- Defined
    patterns = requires(list)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideAssemblages')
class ProvideAssemblages(HandlerProcessor):
    '''
    Provides the assemblages or assemblage support.
    '''
    
    def process(self, chain, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the assemblages.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.patterns, list), 'Invalid support patterns %s' % support.patterns
        
        if obtain.required == Assemblage:
            assemblages = []
            for identifier, types, pattern in support.patterns:
                assemblage = Assemblage()
                assemblage.Id = identifier
                assemblage.Types = types
                assemblages.append(assemblage)
            if obtain.result is None: obtain.result = assemblages
            else: obtain.result = itertools.chain(obtain.result, assemblages)
            return
        
        assert obtain.assemblageId, 'An assemblage id is required'
        
        for identifier, types, pattern in support.patterns:
            if identifier == obtain.assemblageId:
                support.pattern = pattern
                chain.proceed()
                break
