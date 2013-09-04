'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for handling action category service.
'''

from ally.api.error import IdError
from ally.api.type import typeFor
from ally.support.api.util_service import modelId, processCollection
from gui.action.meta.category import WithCategoryAction
from sql_alchemy.support.mapper import MappedSupport, mappingFor
from sql_alchemy.support.util_service import SessionSupport
from sqlalchemy.orm.exc import NoResultFound
from gui.action.core.spec import listCompletePaths, listRootPaths

# --------------------------------------------------------------------

class ActionCategoryServiceAlchemy(SessionSupport):
    '''
    Provides support for handling the action categories. By CATEGORY object is meant the object that has been configured to 
    have the actions mapping on it.
    '''
    
    def __init__(self, Category, CategoryAction):
        '''
        Construct the action category service alchemy.
        
        @param Category: Base class
            The category mapped class that organizes the actions based on.
        @param CategoryAction: class of WithCategoryAction
            The action category relation mapped class.
        '''
        assert isinstance(Category, MappedSupport), 'Invalid mapped class %s' % Category
        assert issubclass(CategoryAction, WithCategoryAction), 'Invalid category action class %s' % CategoryAction
        pks = [pk for pk in mappingFor(Category).columns if pk.primary_key]
        assert pks, 'Cannot detect any primary key for %s' % Category
        assert not len(pks) > 1, 'To many primary keys %s for %s' % (pks, Category)
        
        self.Category = Category
        self.CategoryId = pks[0]
        self.CategoryIdentifier = modelId(Category)
        self.CategoryAction = CategoryAction
    
    def getActions(self, identifier, **options):
        '''
        @see: IActionCategoryPrototype.getActions
        '''
        sql = self.session().query(self.CategoryAction.actionPath).join(self.Category)
        sql = sql.filter(self.CategoryIdentifier == identifier)
        
        return processCollection(listCompletePaths(path for path, in sql.all()), **options)
    
    def getActionsRoot(self, identifier, **options):
        '''
        @see: IActionCategoryPrototype.getActionsRoot
        '''
        sql = self.session().query(self.CategoryAction.actionPath).join(self.Category)
        sql = sql.filter(self.CategoryIdentifier == identifier)
        
        return processCollection(listRootPaths(path for path, in sql.all()), **options)
    
    def getSubActions(self, identifier, parentPath, **options):
        '''
        @see: IActionCategoryPrototype.getSubActions
        '''
        assert isinstance(parentPath, str), 'Invalid parent path %s' % parentPath
        
        sql = self.session().query(self.CategoryAction.actionPath).join(self.Category)
        sql = sql.filter(self.CategoryIdentifier == identifier)
        sql = sql.filter(self.CategoryAction.actionPath.like('%s.%%' % parentPath))
        
        return processCollection(listRootPaths((path for path, in sql.all()), len(parentPath) + 1), **options)
    
    def addAction(self, identifier, actionPath):
        '''
        @see: IActionCategoryPrototype.addAction
        '''
        assert isinstance(actionPath, str), 'Invalid action path %s' % actionPath
        
        sql = self.session().query(self.CategoryId)
        sql = sql.filter(self.CategoryIdentifier == identifier)
        
        try: categoryId, = sql.one()
        except: raise IdError(typeFor(self.Category))
        
        sql = self.session().query(self.CategoryAction)
        sql = sql.filter(self.CategoryAction.actionPath == actionPath).filter(self.CategoryAction.categoryId == categoryId)
        if sql.count() > 0: return
        
        actionCategory = self.CategoryAction()
        actionCategory.actionPath = actionPath
        actionCategory.categoryId = categoryId
        
        self.session().add(actionCategory)
    
    def remAction(self, identifier, actionPath):
        '''
        @see: IActionCategoryPrototype.remAction
        '''
        assert isinstance(actionPath, str), 'Invalid action path %s' % actionPath
        
        sql = self.session().query(self.CategoryAction).join(self.Category)
        sql = sql.filter(self.CategoryIdentifier == identifier).filter(self.CategoryAction.actionPath == actionPath)
        
        try: actionCategory = sql.one()
        except NoResultFound: return False
        
        self.session().delete(actionCategory)
        return True
