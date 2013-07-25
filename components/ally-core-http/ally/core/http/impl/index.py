'''
Created on Apr 17, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP specifications for indexes. 
'''

from ally.core.impl.processor.render.json import createJSONBlockForIndexed, \
    createJSONBlockForContent
from ally.core.impl.processor.render.xml import createXMLBlockForIndexed, \
    createXMLBlockForContent
from ally.indexing.spec.model import Action
from ally.indexing.spec.perform import feedValue

# --------------------------------------------------------------------

NAME_BLOCK_REST = 'rest'  # The block name for REST resources injection from reference URLs.
NAME_BLOCK_CLOB = 'clob'  # The block name for character clobs injection from reference URLs.

ACTION_REFERENCE = 'reference'  # The action name to get the block reference.
ACTION_CHECK_CLOB = 'check_clob'  # The action name to check if the block is for a clob content.
ACTION_ERROR_STATUS = 'error_status'  # The action name for error status.
ACTION_ERROR_MESSAGE = 'error_message'  # The action name for error message.

# --------------------------------------------------------------------

# Provides the HTTP block definitions.
BLOCKS_HTTP = {}

# We provide the XML block definitions.
BLOCKS_HTTP.update(createXMLBlockForIndexed(NAME_BLOCK_REST,
                injectAttributes={ACTION_ERROR_STATUS: 'ERROR', ACTION_ERROR_MESSAGE: 'ERROR_TEXT'},
                captureAttributes={ACTION_REFERENCE: ACTION_REFERENCE}))
BLOCKS_HTTP.update(createXMLBlockForContent(NAME_BLOCK_CLOB,
                Action(ACTION_CHECK_CLOB, feedValue('true'), final=False),
                injectAttributes={ACTION_ERROR_STATUS: 'ERROR', ACTION_ERROR_MESSAGE: 'ERROR_TEXT'},
                captureAttributes={ACTION_REFERENCE: ACTION_REFERENCE}))

# We provide the JSON block definitions.
BLOCKS_HTTP.update(createJSONBlockForIndexed(NAME_BLOCK_REST,
                injectAttributes={ACTION_ERROR_STATUS: 'ERROR', ACTION_ERROR_MESSAGE: 'ERROR_TEXT'},
                captureAttributes={ACTION_REFERENCE: ACTION_REFERENCE}))
BLOCKS_HTTP.update(createJSONBlockForContent(NAME_BLOCK_CLOB,
                Action(ACTION_CHECK_CLOB, feedValue('true'), final=False),
                injectAttributes={ACTION_ERROR_STATUS: 'ERROR', ACTION_ERROR_MESSAGE: 'ERROR_TEXT'},
                captureAttributes={ACTION_REFERENCE: ACTION_REFERENCE}))
