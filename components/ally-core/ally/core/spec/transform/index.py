'''
Created on Apr 17, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides general specifications for indexes. 
'''

# --------------------------------------------------------------------

NAME_BLOCK = 'block'  # The marker name for block.
NAME_ADJUST = 'adjust'  # The marker name for adjust.

# --------------------------------------------------------------------

GROUP_BLOCK = 'block'  # The group name for block.
GROUP_PREPARE = 'prepare'  # The group name for prepare.
GROUP_ADJUST = 'adjust'  # The group name for adjust.

# --------------------------------------------------------------------

ACTION_INJECT = 'inject'  # The action name for inject.
ACTION_CAPTURE = 'capture'  # The action name for capture.

# --------------------------------------------------------------------

PLACE_HOLDER = '${%s}'  # Used for creating place holders.
PLACE_HOLDER_CONTENT = '' # The values entry that marks the proxy side content.

# --------------------------------------------------------------------

# Provides the general markers definitions.
GENERAL_MARKERS = {
                   NAME_BLOCK: dict(group=GROUP_BLOCK),
                   NAME_ADJUST: dict(group=GROUP_ADJUST, action=ACTION_INJECT),
                   }
