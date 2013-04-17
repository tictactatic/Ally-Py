'''
Created on Apr 19, 2012

@package: assemblage
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the decorator to be used by the models in the assemblage domain.
'''

from functools import partial
from ally.api.config import model

# --------------------------------------------------------------------

DOMAIN = 'Assemblage/'
modelAssemblage = partial(model, domain=DOMAIN)
