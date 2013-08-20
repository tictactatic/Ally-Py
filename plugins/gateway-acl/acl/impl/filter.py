'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL filter.
'''

from ..api.filter import IFilterService, Filter, QFilter
from ..meta.acl_intern import Path, Type
from ..meta.filter import FilterMapped, FilterToPath
from ally.api.error import InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.internationalization import _
from ally.support.sqlalchemy.util_service import deleteModel
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityQueryServiceAlchemy, EntitySupportAlchemy
from sqlalchemy.orm.exc import NoResultFound
    
# --------------------------------------------------------------------

@injected
@setup(IFilterService, name='filterService')
class FilterServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, IFilterService):
    '''
    Implementation for @see: IFilterService that provides the ACL filters.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, FilterMapped, QFilter, target=Type.name)
    
    def insert(self, filtre):
        '''
        @see: IFilterService.insert
        '''
        assert isinstance(filtre, Filter), 'Invalid filter %s' % filtre

        dbFilter = FilterMapped()
        dbFilter.Name = filtre.Name
        dbFilter.targetId = self.typeId(filtre.Target)
        
        if filtre.Paths:
            for path in filtre.Paths:
                assert isinstance(path, str), 'Invalid path %s' % path
                if path.count('*') != 1: raise InputError(_('Expected only one *'))
                
                filterToPath = FilterToPath()
                filterToPath.pathId = self.pathId(path)
                dbFilter.paths.append(filterToPath)
        
        self.session().add(dbFilter)
        return dbFilter.Name
        
    def delete(self, name):
        '''
        @see: IFilterService.delete
        '''
        return deleteModel(FilterMapped, name)
    
    # ----------------------------------------------------------------
    
    def pathId(self, path):
        '''
        Provides the path id for the provided path.
        '''
        assert isinstance(path, str), 'Invalid path %s' % path
        
        path = path.strip().strip('/')
        try: pathId, = self.session().query(Path.id).filter(Path.path == path).one()
        except NoResultFound:
            aclPath = Path()
            aclPath.path = path
            
            self.session().add(aclPath)
            self.session().flush((aclPath,))
            pathId = aclPath.id
        
        return pathId
    
    def typeId(self, name):
        '''
        Provides the type id for the provided type name.
        '''
        assert isinstance(name, str), 'Invalid type name %s' % name
        
        name = name.strip()
        try: typeId, = self.session().query(Type.id).filter(Type.name == name).one()
        except NoResultFound:
            aclType = Type()
            aclType.name = name
            self.session().add(aclType)
            self.session().flush((aclType,))
            typeId = aclType.id
        return typeId
