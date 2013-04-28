'''
Created on Apr 19, 2012

@package: indexing
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the decorator to be used by the models in the indexing domain.
'''

from ally.api.config import model
from functools import partial

# --------------------------------------------------------------------

DOMAIN = 'Indexing/'
modelIndexing = partial(model, domain=DOMAIN)
