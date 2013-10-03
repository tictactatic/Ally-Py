'''
Created on Sep 14, 2012

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mugur Rus

Contains ZIP utils
'''

from ally.container.event import Trigger
from ally.support.util_io import synchronizeURIToDir
from ally.zip.util_zip import getZipFilePath, validateInZipPath, ZIPSEP
from os.path import join, isdir
from platform import system, machine, system_alias, release, version, \
    linux_distribution
from zipfile import ZipFile

# --------------------------------------------------------------------

SYSTEM_ALL = 'all'
MACHINE_ALL = 'all'

# --------------------------------------------------------------------

def systemInfo():
    '''
    Returns a tuple containing the following information:
    - system name (e.g. Darwin, Windows, Ubuntu etc.)
    - release (e.g.: 12.04 for Ubuntu, 11.4.0 for Darwin etc.)
    - version
    The difference between platform.system_alias() and this function is that
    this function returns the Linux distribution name and version instead of
    'Linux' and the kernel version.
    '''
    sys, rel, ver = system_alias(system(), release(), version())
    if sys == 'Linux':
        sys, rel, _relname = linux_distribution()
    return (sys, rel, ver)

def deploy(source, destination, systemName=None, machineName=None):
    '''
    Deploys the tool found at the source directory to the destination directory.

    @param source: src
        The directory from which to deploy the tool
    @param destination: src
        The path where to deploy the tool
    @param systemName: src
        The name of the system for which to deploy (e.g. Darwin, Windows, Ubuntu)
    @param machineName: src
        The machine name (e.g.: x86, x86_64)
    @return: tuple
        Tuple containing the system information (name, release, version) and True
        if the tool was deployed, False if it wasn't
    '''
    # TODO: This should not be placed here a separate plugin needs to be created.
    assert isinstance(source, str), 'Invalid source path %s' % source
    assert isinstance(destination, str), 'Invalid destination path %s' % destination
    assert not systemName or isinstance(systemName, str), 'Invalid system name %s' % systemName
    assert not machineName or isinstance(machineName, str), 'Invalid machine name %s' % machineName

    if not systemName: systemName, rel, ver = systemInfo()
    machineName = machineName if machineName else machine()

    systems = (SYSTEM_ALL) if systemName == SYSTEM_ALL else (systemName, SYSTEM_ALL)
    machines = (MACHINE_ALL) if machineName == MACHINE_ALL else (machineName, MACHINE_ALL)

    deployed = False
    for systemName in systems:
        for machineName in machines:
            srcDir = join(source, systemName, machineName)
            if not isdir(srcDir):
                try:
                    zipPath, inPath = getZipFilePath(srcDir)
                    validateInZipPath(ZipFile(zipPath), inPath + ZIPSEP)
                except (IOError, KeyError): continue
            synchronizeURIToDir(srcDir, destination)
            deployed = True

    return (systemName, rel, ver, deployed)

# --------------------------------------------------------------------
    
PREPARE = Trigger('prepare')
# Trigger used for controlled event prepare deployment setup functions.
DEPLOY = Trigger('deploy')
# Trigger used for controlled event deployment setup functions.

class Options:
    '''
    Provides the container for arguments options.
    '''
    
    def __init__(self):
        '''
        Construct the options.
        '''
        self._flagsRegistered = {}
        self._flags = set()
        
    def registerFlag(self, name, *invalidate):
        '''
        Register a flag with the provided name.
        
        @param name: string
            The flag name to register.
        @param invalidate: arguments[string]
            The flag names to invalidate (set to False) if this flag is set to True.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        if __debug__:
            for fname in invalidate: assert isinstance(fname, str), 'Invalid invalidate flag name %s' % fname
        self._flagsRegistered[name] = invalidate
        
    def registerFlagTrue(self, name, *invalidate):
        '''
        Register a flag with the provided name that is by default true.
        
        @param name: string
            The flag name to register.
        @param invalidate: arguments[string]
            The flag names to invalidate (set to False) if this flag is set to True.
        '''
        self.registerFlag(name)
        self._flags.add(name)
    
    def isFlag(self, name):
        '''
        Checks if the flag is set.
        
        @param name: string
            The flag name to check.
        @return: boolean
            True if the flag is set, False otherwise
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        return name in self._flags
    
    def __setattr__(self, name, value):
        assert isinstance(name, str), 'Invalid name %s' % name
        if name.startswith('_') or name not in self._flagsRegistered: object.__setattr__(self, name, value)
        elif value:
            self._flags.difference_update(self._flagsRegistered[name])
            self._flags.add(name)
        else: self._flags.discard(name)
