'''
Created on Jul 12, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides encoder decoder specifications. 
'''

from ally.core.spec.transform.encdec import Category

# --------------------------------------------------------------------

CATEGORY_HEADER = Category('The available headers', optional=True)
# The constant that defines the headers decoding category.

CATEGORY_PARAMETER = Category('The available parameters', optional=True)
# The constant that defines the parameters decoding category.
SEPARATOR_PARAMETERS = '.'
# The separator for parameters.

# --------------------------------------------------------------------
