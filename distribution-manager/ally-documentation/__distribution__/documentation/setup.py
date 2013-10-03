'''
Created on Oct 2, 2013

@package: ally documentation
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for documentation.
'''

from ..general.setup import FLAG_PACKAGE
from .service import path_location, generator, path_template
from ally.container import event, support
from ally.support.util_deploy import Options, PREPARE, DEPLOY
from argparse import ArgumentParser
import distribution
import os

# --------------------------------------------------------------------

FLAG_DOCUMENT = 'document'
# Flag indicating the documentation action.

# --------------------------------------------------------------------

@event.on(PREPARE)
def prepare():
    assert isinstance(distribution.parser, ArgumentParser), 'Invalid distribution parser %s' % distribution.parser
    assert isinstance(distribution.options, Options), 'Invalid distribution options %s' % distribution.options
    
    distribution.options.template = None
    
    distribution.options.registerFlag(FLAG_DOCUMENT, FLAG_PACKAGE)
    distribution.parser.add_argument('-doc', dest=FLAG_DOCUMENT, action='store_true',
                                     help='requires API data\n.Provide this option in order to create documentation at the '
                                     'provided --location, if no location is provided it will default to the current folder.')
    distribution.parser.add_argument('--template', metavar='folder', dest='template', help='The location where '
                                     'the documentation templates are located, if not provided it will default to "template" '
                                     'folder inside the --location.')

@event.on(DEPLOY)
def deploy():
    if distribution.options.isFlag(FLAG_DOCUMENT):
        location = getattr(distribution.options, 'location', None)
        if location: support.force(path_location, location)
        template = getattr(distribution.options, 'template', None)
        if template: support.force(path_template, template)
        elif location: support.force(path_template, os.path.join(location, 'template'))
            
        generator().process()
