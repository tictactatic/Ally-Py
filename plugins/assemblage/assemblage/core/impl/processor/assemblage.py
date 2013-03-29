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
from ally.core.spec.transform.representation import Attribute
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
    # ---------------------------------------------------------------- Required
    patterns = requires(dict)
    
class Pattern(Context):
    '''
    The pattern context.
    '''
    # ---------------------------------------------------------------- Required
    contentTypes = requires(tuple)
    pattern = requires(IPattern)
    adjusters = requires(tuple)

# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideAssemblages')
class ProvideAssemblages(HandlerProcessor):
    '''
    Provides the assemblages or assemblage support.
    '''
    
    error_attributes = ['ERROR', 'ERROR_TEXT']
    # The names of the error attributes to be injected in failed matchers.
    
    def __init__(self):
        assert isinstance(self.error_attributes, list), 'Invalid error attributes %s' % self.error_attributes
        super().__init__(Pattern=Pattern)
        
        self._attributes = [Attribute(name) for name in self.error_attributes]
    
    def process(self, chain, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the assemblages.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.patterns, dict), 'Invalid support patterns %s' % support.patterns
        
        if obtain.required == Assemblage:
            assemblages = []
            for identifier, pattern in support.patterns.items():
                assert isinstance(pattern, Pattern), 'Invalid pattern %s' % pattern
                assert isinstance(pattern.pattern, IPattern), 'Invalid pattern %s' % pattern
                
                assemblage = Assemblage()
                assemblage.Id = identifier
                assemblage.Types = pattern.contentTypes

                if assemblage.AdjustReplace is None: assemblage.AdjustReplace = []
                if assemblage.AdjustPattern is None: assemblage.AdjustPattern = []
                for areplace, apattern in pattern.adjusters:
                    assert isinstance(areplace, str), 'Invalid replace %s' % areplace
                    assert isinstance(apattern, str), 'Invalid pattern %s' % apattern
                    assemblage.AdjustReplace.append(areplace)
                    assemblage.AdjustPattern.append(apattern)
                
                if assemblage.ErrorReplace is None: assemblage.ErrorReplace = {}
                if assemblage.ErrorPattern is None: assemblage.ErrorPattern = {}
                for attr in self._attributes:
                    assert isinstance(attr, Attribute)
                    ireplace, ipattern = pattern.pattern.injector(attr)
                    assemblage.ErrorReplace[attr.name] = ireplace
                    assemblage.ErrorPattern[attr.name] = ipattern
                
                assemblages.append(assemblage)
            if obtain.result is None: obtain.result = assemblages
            else: obtain.result = itertools.chain(obtain.result, assemblages)
            return
        
        assert obtain.assemblageId, 'An assemblage id is required'
        
        pattern = support.patterns.get(obtain.assemblageId)
        if pattern:
            assert isinstance(pattern, Pattern), 'Invalid pattern %s' % pattern
            support.pattern = pattern.pattern
            chain.proceed()
