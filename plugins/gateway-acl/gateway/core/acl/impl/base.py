'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, CONSUMED

# --------------------------------------------------------------------

ACTION_GET = 'get'  # The get value action.
ACTION_ADD = 'add'  # The add action.
ACTION_DEL = 'delete'  # The delete action.

# --------------------------------------------------------------------

class RequireSolicit(Context):
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
    # ---------------------------------------------------------------- Required
    value = requires(object)

# --------------------------------------------------------------------

def getSolicit(manage, target, **data):
    '''
    Gets the value for the solicit.
    
    @param target: object
        The target to get the value for.
    @param data: key arguments
        For data key arguments to be used for fetching the names.
    @return: object
        The value for the provided arguments.
    '''
    assert isinstance(manage, Processing), 'Invalid processing %s' % manage
    solicit = manage.execute(solicit=manage.ctx.solicit(action=ACTION_GET, target=target, **data)).solicit
    assert isinstance(solicit, RequireSolicit), 'Invalid solicit %s' % solicit
    return solicit.value

def addSolicit(manage, target, **data):
    '''
    Adds a new entry for the target using the provided data.
        
    @param target: class
        The target class to fetch the names for.
    @param data: key arguments
        For data key arguments to be used for adding.
    @return: boolean
        True if the adding has been done successfully, False otherwise.
    '''
    assert isinstance(manage, Processing), 'Invalid processing %s' % manage
    done, _arg = manage.execute(CONSUMED, solicit=manage.ctx.solicit(action=ACTION_ADD, target=target, **data))
    return done

def remSolicit(manage, target, **data):
    '''
    Removes the entry for the target using the provided data.
    
    @param target: class
        The target class to fetch the names for.
    @param data: key arguments
        For data key arguments to be used for removing.
    @return: boolean
        True if the removing has been done successfully, False otherwise.
    '''
    assert isinstance(manage, Processing), 'Invalid processing %s' % manage
    done, _arg = manage.execute(CONSUMED, solicit=manage.ctx.solicit(action=ACTION_DEL, target=target, **data))
    return done
