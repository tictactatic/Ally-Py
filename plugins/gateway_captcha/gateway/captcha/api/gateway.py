'''
Created on Jan 28, 2013

@package: captcha
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for captcha gateway .
'''

from ally.api.config import service, call
from ally.api.type import Iter
from gateway.api.gateway import Gateway

# --------------------------------------------------------------------

@service
class IGatewayCaptchaService:
    '''
    The gateway service that provides the captcha accesses.
    '''

    @call(webName='Captcha')
    def getCaptcha(self) -> Iter(Gateway):
        '''
        Get the gateway options that apply for an captcha accesses.
        '''
