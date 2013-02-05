'''
Created on Feb 2, 2012

@package ally core request
@copyright 2011 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Contains the GUI configuration setup for the node presenter plugin.
'''

from ..gui_core import publish_gui_resources
from ..gui_core.gui_core import getPublishedLib, gui_folder_format
from ..plugin.registry import cdmGUI
from .gui_core import getGuiPath, lib_folder_format, publishLib
from ally.container import ioc
from ally.support.util_io import openURI
from distribution.container import app
from io import BytesIO
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.config
def js_core_libs_format():
    ''' The javascript bootstrap relative filename '''
    return 'scripts/js/%s.js'

@ioc.config
def js_core_libs():
    ''' The javascript core libraries '''
    return ['main']

@ioc.config
def js_bootstrap_file():
    ''' The javascript core libraries '''
    return 'scripts/js/startup.js'

@ioc.config
def ui_demo_file():
    ''' the demo client html file '''
    return 'start.html'

@ioc.config
def server_url():
    ''' for demo file update... '''
    return 'localhost:8080'

# --------------------------------------------------------------------

@app.populate
def publish():
    publishLib('core')

@ioc.after(publish)
def updateStartup():
    if not publish_gui_resources(): return  # No publishing is allowed
    bootPath = lib_folder_format() % 'core/'
    fileList = []
    for x in js_core_libs():
        try: fileList.append(openURI(getGuiPath(js_core_libs_format() % x)))
        except: pass

    try: cdmGUI().remove(bootPath + js_bootstrap_file())
    except: pass
    cdmGUI().publishContent(bootPath + js_bootstrap_file(), BytesIO(b'\n'.join([fi.read() for fi in fileList])))

    for f in fileList: f.close()
