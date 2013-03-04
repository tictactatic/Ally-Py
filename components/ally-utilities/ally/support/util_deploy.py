'''
Created on Sep 14, 2012

@package ally utilities
@copyright 2012 Sourcefabric o.p.s.
@license http: // www.gnu.org / licenses / gpl - 3.0.txt
@author: Mugur Rus

Contains ZIP utils
'''

from os.path import join, isdir
from ally.support.util_io import synchronizeURIToDir
from ally.zip.util_zip import getZipFilePath
from platform import system, machine, system_alias, release, version, \
    linux_distribution

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

    systems = {SYSTEM_ALL:False} if systemName == SYSTEM_ALL else {systemName:True, SYSTEM_ALL:False}
    machines = {MACHINE_ALL:False} if machineName == MACHINE_ALL else {machineName:True, MACHINE_ALL:False}

    deployed = False
    for systemName, _systemRequired in systems.items():
        for machineName, _machineRequired in machines.items():
            srcDir = join(source, systemName, machineName)
            if not isdir(srcDir):
                try: getZipFilePath(srcDir)
                except IOError: continue
#                    if systemRequired and machineRequired:
#                        raise IOError('Cannot locate required dependency \'%s\' for system %s with architecture %s'
#                                      % (srcDir, systemName, machineName))
#                    else: continue
            synchronizeURIToDir(srcDir, destination)
            deployed = True

    return (systemName, rel, ver, deployed)
