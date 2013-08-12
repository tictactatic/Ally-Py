'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL management.
'''

from ..spec import IACLManagement, ACTION_GET, ACTION_ADD, ACTION_DEL
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, CONSUMED

# --------------------------------------------------------------------

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    action = defines(str, doc='''
    @rtype: string
    The action to perform.
    ''')
    target = defines(object, doc='''
    @rtype: object
    The target object to get.
    ''')
    forAccess = defines(str, doc='''
    @rtype: string
    The access name to be handled.
    ''')
    forMethod = defines(str, doc='''
    @rtype: string
    The method name to be handled.
    ''')
    forGroup = defines(str, doc='''
    @rtype: string
    The group name to be handled.
    ''')
    forFilter = defines(str, doc='''
    @rtype: string
    The filter name to be handled.
    ''')
    # ---------------------------------------------------------------- Required
    value = requires(object)

# --------------------------------------------------------------------

@injected
@setup(IACLManagement, name='aclManagement')
class ACLManagement(IACLManagement):
    '''
    Implementation for @see: IMethodService that provides the ACL access method setup support.
    '''
    
    assemblyACLManagement = Assembly; wire.entity('assemblyACLManagement')
    # The assembly to be used for managing.
    
    def __init__(self):
        assert isinstance(self.assemblyACLManagement, Assembly), 'Invalid assembly management %s' % self.assemblyACLManagement
        
        self._manage = self.assemblyACLManagement.create(solicit=Solicit)
    
    def get(self, target, **data):
        '''
        @see: IACLManagement.get
        '''
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        
        solicit = manage.execute(solicit=manage.ctx.solicit(action=ACTION_GET, target=target, **data)).solicit
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        return solicit.value
    
    def add(self, target, **data):
        '''
        @see: IACLManagement.add
        '''
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        done, _arg = manage.execute(CONSUMED, solicit=manage.ctx.solicit(action=ACTION_ADD, target=target, **data))
        return done

    def remove(self, target, **data):
        '''
        @see: IACLManagement.remove
        '''
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        done, _arg = manage.execute(CONSUMED, solicit=manage.ctx.solicit(action=ACTION_DEL, target=target, **data))
        return done
