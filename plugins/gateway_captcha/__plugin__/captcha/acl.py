'''
Created on Jan 15, 2013

@package: captcha
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the acl captcha setup.
'''

from acl.right_sevice import RightService
from ally.container import ioc
from ally.internationalization import NC_

# --------------------------------------------------------------------

@ioc.entity
def captcha() -> RightService:
    return RightService('CAPTCHA', NC_('security', 'Right that targets CAPTCHA validations'))
