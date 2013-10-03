'''
Created on Oct 2, 2013

@package: ally documentation
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the creation of documentation based on wheezy template engine.
'''

from ally.container.ioc import injected
from ally.support.http.request import RequesterGetJSON
from jinja2 import Environment, FileSystemLoader
import logging
import os
import re
import sys

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
class DocumentGenerator:
    '''
    Provides the documentation based on wheezy template engine.
    '''
    
    pathTemplate = str
    # The path where the template files are located.
    pathLocation = str
    # The location path where to dump the documentation.
    
    requesterGetJSON = RequesterGetJSON
    # The requester for getting the administration plugin data.
    
    excludePattern = '.+\~$'
    # The rgex used for excluding template files.
    modelFolder = 'model'
    # The folder where the model templates are located.
    indexFolder = 'index'
    # The folder where the index templates are located.
    
    def __init__(self):
        assert isinstance(self.pathTemplate, str), 'Invalid template path %s' % self.pathTemplate
        assert isinstance(self.pathLocation, str), 'Invalid location path %s' % self.pathLocation
        assert isinstance(self.requesterGetJSON, RequesterGetJSON), 'Invalid requester JSON %s' % self.requesterGetJSON
        assert isinstance(self.excludePattern, str), 'Invalid exclude pattern %s' % self.excludePattern
        assert isinstance(self.modelFolder, str), 'Invalid model folder %s' % self.modelFolder
        assert isinstance(self.indexFolder, str), 'Invalid index folder %s' % self.indexFolder
        
        if not os.path.exists(self.pathTemplate):
            log.error('The template path \'%s\' does not exist.', self.pathTemplate)
            sys.exit()
        if not os.path.exists(self.pathLocation): os.makedirs(self.pathLocation)
        
        self.loader = FileSystemLoader(self.pathTemplate)
        self.environment = Environment(loader=self.loader)
        self.reexclude = re.compile(self.excludePattern)
        
    def process(self):
        '''
        Process the documentation.
        '''
        modelPaths, modelIndexPaths = [], []

        modelIndexFolder = os.path.join(self.modelFolder, self.indexFolder)
        for path in self.loader.list_templates():
            if self.reexclude.match(path): continue
            
            dirName = os.path.dirname(path) 
            if dirName == self.modelFolder: modelPaths.append(path)
            elif dirName == modelIndexFolder: modelIndexPaths.append(path)
        
        if modelPaths or modelIndexPaths:
            obj = self.requesterGetJSON.request('resources/Admin/Model?asc=name',
                                                headers={'X-Filter': 'Model.*,Model.ModelProperty.Property.*'})
            if obj is None:
                log.error('Cannot get the model API data')
                return False
            
            for path in modelIndexPaths:
                template = self.environment.get_template(path)
                location = path.replace(os.sep, '_')
                location = os.path.join(self.pathLocation, location)
                with open(location, 'w') as f: f.write(template.render(models=obj['ModelList']))
                
            for model in obj['ModelList']:
                for path in modelPaths:
                    template = self.environment.get_template(path)
                    location = path.replace(os.sep, '_')
                    location = location.replace('*', model['API'].replace('.', '_'))
                    location = os.path.join(self.pathLocation, location)
                    with open(location, 'w') as f: f.write(template.render(model=model))
                    
        else: log.warn('No model templates to process')
