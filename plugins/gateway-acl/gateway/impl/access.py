'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access.
'''

from ..api.access import IAccessService, Access
from ally.api.error import InputError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, CONSUMED
from ally.internationalization import _

# --------------------------------------------------------------------

class Allow(Context):
    '''
    The allow context.
    '''
    # ---------------------------------------------------------------- Defined
    group = defines(str, doc='''
    @rtype: string
    The access group to allow the access for.
    ''')
    pattern = defines(str, doc='''
    @rtype: string
    The URI pattern to allow access for.
    ''')
    method = defines(str, doc='''
    @rtype: string
    The HTTP method name to allow access for.
    ''')
    # ---------------------------------------------------------------- Required
    id = requires(str)
    suggestion = requires(tuple)
    methodsAllowed = requires(set)

# --------------------------------------------------------------------

@injected
@setup(IAccessService, name='accessService')
class AccessService(IAccessService):
    '''
    Implementation for @see: IAccessService that provides the ACL access setup support.
    '''
    
    assemblyManageAccess = Assembly; wire.entity('assemblyManageAccess')
    # The assembly to be used for managing access.
    
    def __init__(self):
        assert isinstance(self.assemblyManageAccess, Assembly), 'Invalid assembly manage access %s' % self.assemblyManageAccess
        self._manage = self.assemblyManageAccess.create(allow=Allow)
    
    def getGroups(self):
        '''
        @see: IAccessService.getGroups
        '''
        
    def allow(self, name, access):
        '''
        @see: IAccessService.allow
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(access, Access), 'Invalid access %s' % access
        
        manage = self._manage
        assert isinstance(manage, Processing), 'Invalid processing %s' % manage
        
        done, arg = manage.execute(CONSUMED, allow=manage.ctx.allow(group=name, pattern=access.Pattern, method=access.Method))
        assert isinstance(arg.allow, Allow), 'Invalid allow %s' % arg.allow
        if done:
            # TODO: remove
            print(arg.allow.id)
        elif arg.allow.methodsAllowed:
            raise InputError(_('Only allowed methods %(methods)s'), Access.Method, methods=sorted(arg.allow.methodsAllowed))
        elif arg.allow.suggestion:
            msg, data = arg.allow.suggestion
            raise InputError(msg, Access.Pattern, **data)
        else:
            raise InputError(_('Invalid pattern'), Access.Pattern)
            
    def remove(self, name, id):
        '''
        @see: IAccessService.remove
        '''
