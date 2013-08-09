'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL management.
'''

from ..spec import IACLManagement
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, CONSUMED

# --------------------------------------------------------------------
    
class Get(Context):
    '''
    The get context.
    '''
    # ---------------------------------------------------------------- Defined
    target = defines(object, doc='''
    @rtype: object
    The target object to get.
    ''')
    forName = defines(str, doc='''
    @rtype: string
    The entity name to fetch, destination in 'entity'.
    ''')
    forAccess = defines(str, doc='''
    @rtype: string
    The access name to fetch the entities for, destination in 'names'.
    ''')
    forGroup = defines(str, doc='''
    @rtype: string
    The group name to fetch the entities for, attention this is only considered if a 'forAccess' is provided,
    destination in 'names'.
    ''')
    forMethod = defines(str, doc='''
    @rtype: string
    The access name to fetch the entities for, attention this is only considered if a 'forAccess' is provided,
    destination in 'names'.
    ''')
    forAll = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that all entities names should be provided, destination in 'names'. 
    ''')
    # ---------------------------------------------------------------- Required
    value = requires(object)

class Alter(Context):
    '''
    The alter context.
    '''
    # ---------------------------------------------------------------- Defined
    target = defines(type, doc='''
    @rtype: class
    The target entity to alter.
    ''')
    access = defines(str, doc='''
    @rtype: string
    The access name to alter for.
    ''')
    group = defines(str, doc='''
    @rtype: string
    The group name to alter for.
    ''')
    method = defines(str, doc='''
    @rtype: string
    The method name to alter for.
    ''')
    filter = defines(str, doc='''
    @rtype: string
    The filter name to alter for.
    ''')
    
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
        
        self._manage = self.assemblyACLManagement.create(get=Get, add=Alter, remove=Alter)
    
    def get(self, target, **forData):
        '''
        @see: IACLManagement.get
        '''
        assert forData, 'At least one for data key argument is required'
        
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        
        get = manage.execute(get=manage.ctx.get(target=target, **forData)).get
        assert isinstance(get, Get), 'Invalid get method %s' % get
        return get.value
    
    def add(self, target, **data):
        '''
        @see: IACLManagement.add
        '''
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        done, _arg = manage.execute(CONSUMED, add=manage.ctx.add(target=target, **data))
        return done

    def remove(self, target, **data):
        '''
        @see: IACLManagement.remove
        '''
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        done, _arg = manage.execute(CONSUMED, remove=manage.ctx.remove(target=target, **data))
        return done
