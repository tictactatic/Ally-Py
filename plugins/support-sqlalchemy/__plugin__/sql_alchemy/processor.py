'''
Created on Aug 19, 2013

@package: support sqlalchemy
@copyright: 2011 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for general SQL alchemy processors.
'''

from ally.container import ioc
from ally.design.processor.handler import Handler
from sql_alchemy.impl.processor.transaction import TransactionHandler

# --------------------------------------------------------------------

@ioc.entity
def transaction() -> Handler: return TransactionHandler()