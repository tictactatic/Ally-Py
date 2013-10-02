'''
Created on Aug 18, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL internal mappings.
'''

from .metadata_acl import Base
from sql_alchemy.support.session import openSession
from sql_alchemy.support.util_meta import joinedExpr, hybrid
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import String

# --------------------------------------------------------------------

class Path(Base):
    '''
    Provides the ACL path mapping.
    '''
    __tablename__ = 'acl_path'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    path = Column('path', String(255), nullable=False, unique=True)
    priority = Column('priority', INTEGER(unsigned=True))
    # Provides the priority of access objects in creating gateways.
    
class Method(Base):
    '''
    Provides the ACL method mapping.
    '''
    __tablename__ = 'acl_method'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    name = Column('name', String(20), nullable=False, unique=True)

class Signature(Base):
    '''
    Provides the ACL type signature mapping.
    '''
    __tablename__ = 'acl_signature'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    name = Column('name', String(255), nullable=False, unique=True)

# --------------------------------------------------------------------

class WithPath:
    '''
    Provides the definition used to add path on other mappings.
    '''

    pathId = declared_attr(lambda cls: Column('fk_path_id', ForeignKey(Path.id, ondelete='RESTRICT'), nullable=False))
    path = declared_attr(lambda cls: relationship(Path, lazy='joined', uselist=False, viewonly=True))

    @hybrid(expr=joinedExpr(Path, 'path'))
    def Path(self):
        if self.path: return self.path.path
    @Path.setter
    def PathSet(self, path):
        assert isinstance(path, str), 'Invalid path %s' % path
        path = path.strip().strip('/')
        session = openSession()
        try: pathId, = session.query(Path.id).filter(Path.path == path).one()
        except NoResultFound:
            aclPath = Path()
            aclPath.path = path
            
            for k, item in enumerate(path.split('/'), 1):
                if item == '*' and aclPath.priority is None:
                    aclPath.priority = k
                    break
            if aclPath.priority is None: aclPath.priority = 0
            
            session.add(aclPath)
            session.flush((aclPath,))
            pathId = aclPath.id
        self.pathId = pathId
    
class WithMethod:
    '''
    Provides the definition used to add method on other mappings.
    '''
    
    methodId = declared_attr(lambda cls: Column('fk_method_id', ForeignKey(Method.id, ondelete='RESTRICT'), nullable=False))
    method = declared_attr(lambda cls: relationship(Method, lazy='joined', uselist=False, viewonly=True))
    
    @hybrid(expr=joinedExpr(Method, 'name'))
    def Method(self):
        if self.method: return self.method.name
    @Method.setter
    def MethodSet(self, name):
        assert isinstance(name, str), 'Invalid name %s' % name
        name = name.strip().upper()
        assert name, 'Empty string is not a valid name'
        
        session = openSession()
        try: methodId, = session.query(Method.id).filter(Method.name == name).one()
        except NoResultFound:
            method = Method()
            method.name = name
            session.add(method)
            session.flush((method,))
            methodId = method.id
        self.methodId = methodId

class WithSignature:
    '''
    Provides the definition used to add signature on other mappings.
    '''
    
    signatureId = declared_attr(lambda cls:
                                Column('fk_signature_id', ForeignKey(Signature.id, ondelete='RESTRICT'), nullable=False))
    signature = declared_attr(lambda cls: relationship(Signature, lazy='joined', uselist=False, viewonly=True))
    
    @classmethod
    def createSignature(cls):
        '''
        Create the signature name link.
        '''
        
        def fget(self):
            if self.signature: return self.signature.name
        
        def fset(self, name):
            assert isinstance(name, str), 'Invalid signature name %s' % name
            name = name.strip()
            assert name, 'Empty string is not a valid signature name'
            
            session = openSession()
            try: signatureId, = session.query(Signature.id).filter(Signature.name == name).one()
            except NoResultFound:
                signature = Signature()
                signature.name = name
                session.add(signature)
                session.flush((signature,))
                signatureId = signature.id
            self.signatureId = signatureId
            
        return hybrid_property(fget, fset, expr=joinedExpr(Signature, 'name'))
