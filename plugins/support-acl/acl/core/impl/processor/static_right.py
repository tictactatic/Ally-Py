'''
Created on Jun 7, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds static rights.
'''

from acl.spec import RightAcl
from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Iterable
import itertools

# --------------------------------------------------------------------

class Solicitation(Context):
    '''
    The solicitation context.
    '''
    # ---------------------------------------------------------------- Defined
    rights = defines(Iterable, doc='''
    @rtype: Iterable(RightAcl)
    The static rights for the types.
    ''')
    
# --------------------------------------------------------------------

@injected
class RegisterStaticRights(HandlerProcessorProceed):
    '''
    The handler that populates static rights.
    '''
    
    rights = list
    # The static rights to populate
    
    def __init__(self):
        assert isinstance(self.rights, list), 'Invalid static rights %s' % self.rights
        if __debug__:
            for right in self.rights: assert isinstance(right, RightAcl), 'Invalid right %s' % right
        super().__init__()
    
    def process(self, solicitation:Solicitation, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Adds the default rights.
        '''
        assert isinstance(solicitation, Solicitation), 'Invalid solicitation %s' % solicitation
        
        if solicitation.rights is not None: solicitation.rights = itertools.chain(solicitation.rights, self.rights)
        else: solicitation.rights = iter(self.rights)
