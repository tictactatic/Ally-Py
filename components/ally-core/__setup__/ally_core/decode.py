'''
Created on Jun 16, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ally.container import ioc
from ally.core.impl.processor.decoder.primitive import PrimitiveDecode
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def primitiveDecode() -> Handler: return PrimitiveDecode()
