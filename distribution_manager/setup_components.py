'''
Created on Sep 30, 2013
 
@package: distribution manager
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Cristian Domsa
 
Simple implementation for distribution manager project.
'''

import os
import sys
import logging 

# --------------------------------------------------------------------

SETUP_FILENAME = 'setup.py'
SETUP_TEMPLATE_BEGIN = '''
\'\'\'
Created on Oct 1, 2013
 
@package: distribution_manager
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Cristian Domsa
 
Setup configuration for components/plugins needed for pypi.
\'\'\'

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup('''
SETUP_TEMPLATE_END = '''packages=find_packages('.'),
      platforms=['all'],
      zip_safe=True,
      license='GPL v3',
      url='http://www.sourcefabric.org/en/superdesk/', # project home page
      )
'''
COMPONENTS_DIR = '../components'
IGNORE_DIRS = ['__pycache__']
ATTRIBUTE_MAPPING = {'NAME'            : 'name',
                     'VERSION'         : 'version',
                     'AUTHOR'          : 'author',
                     'AUTHOR_EMAIL'    : 'author_email',
                     'KEYWORDS'        : 'keywords',
                     'INSTALL_REQUIRES': 'install_requires',
                     'DESCRIPTION'     : 'description',
                     'LONG_DESCRIPTION': 'long_desciption',
                     'TEST_SUITE'      : 'test_suite',
                     'CLASSIFIERS'     : 'classifiers',
                     }
EXTRA_DICT_ATT = '__extra__'

# --------------------------------------------------------------------

class Distribution:
    '''
    @todo: update description
    Distribution class for managing requirements, deploy path
    '''
    def __init__(self, path):
        
        assert isinstance(path, str), 'Invalid path provided %s' % path
        self.path = path

    def getDirs(self, path):
        '''
        returns the list of directories filtering out IGNORE_DIRS
        '''
        children = os.listdir(path)
        return [child for child in children if os.path.isdir(os.path.join(path, child)) 
                                            and child not in IGNORE_DIRS]

    def constructDict(self, module):
        '''
        returns the dict containing information contained in __init__ file
        @purpose: setuptools 
        '''
        
        assert isinstance(module, ), 'Invalid module name '
        setupDict = {}
        for attribute, value in ATTRIBUTE_MAPPING.items():
            if hasattr(module, attribute):
                setupDict[value] = getattr(module, attribute)
        if hasattr(module, EXTRA_DICT_ATT):
            setupDict.update(getattr(module, EXTRA_DICT_ATT))
        return setupDict
    
    def writeSetupFile(self, path, info):
        '''
        Writes setup.py file to path
        '''
        filename = os.path.abspath(os.path.join(path, SETUP_FILENAME))
        with open(filename, 'w') as f:
            f.write(SETUP_TEMPLATE_BEGIN)
            for attribute in info:
                f.write(attribute + '=' + repr(info[attribute]) + ',\n')
            f.write(SETUP_TEMPLATE_END)
        f.close()
 
    def generateSetupFiles(self):
        
        all = success = failed = 0
        components = self.getDirs(self.path)
 
        for packageName in components:
            all += 1
            assert logging.info('-' * 50) or True
            assert logging.info('*** Package name *** {0} ***'.format(packageName)) or True
            packagePath = os.path.join(COMPONENTS_DIR, packageName)
            if '__setup__' in self.getDirs(packagePath):
                setupPath = os.path.join(COMPONENTS_DIR, packageName, '__setup__')
                setupDirs = self.getDirs(setupPath)
                sys.path.append(os.path.abspath(setupPath))
                if len(setupDirs) != 1:
                    assert logging.info('''No setup module to configure or 
                            more than one setup module in this package 
                            *** SKIPING *** {0) ***'''.format(packageName)) or True
                    continue
                else:
                    setupModule = setupDirs[0] 
                    try:
                        module = __import__(setupModule, locals=locals(), globals=globals())
                        try: 
                            info = self.constructDict(module)
                            self.writeSetupFile(packagePath, info)
                            assert logging.info('*** File succesfully writen *** {0} *** OK'.format(packagePath)) or True
                        except: 
                            assert logging.info('*** File writing failed *** {0} *** NOK'.format(packagePath)) or True
                        assert logging.info('*** Setup module *** {0} *** OK'.format(setupModule)) or True
                        success += 1
                    except: 
                        assert logging.info('*** Setup module *** {0} *** NOK'.format(setupModule)) or True
                        failed += 1
        
        assert logging.info('-' * 50) or True                
        assert logging.info('All components: {0}'.format(all)) or True
        assert logging.info('Succeded: {0}'.format(success)) or True
        assert logging.info('Failed: {0}'.format(failed)) or True
        print('***All:{0}***Succ:{1}***Fail:{2}***'.format(all, success, failed))


if __name__ == '__main__':
    
    dist = Distribution(COMPONENTS_DIR)
    dist.generateSetupFiles()