'''
Created on Aug 20, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides priorities.
'''

from ally.design.priority import Priority, PRIORITY_NORMAL

# --------------------------------------------------------------------

PRIORITY_LOAD_ENTITIES = Priority('Load all entities', after=PRIORITY_NORMAL)
# The priority for @see: loadAllEntities.
