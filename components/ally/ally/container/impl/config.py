'''
Created on Jan 11, 2012

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides configurations serializing support.
'''

from io import StringIO
import re

# --------------------------------------------------------------------

REGEX_SPLIT = re.compile('[\n]+')
# Regex used in spliting the descriptions for wrapping

# --------------------------------------------------------------------

def save(configurations, fwrite, maxwidth=60):
    '''
    Saves the configurations to the provided file writer.
    
    @param configurations: dictionary{string, Config}
        A dictionary of the configurations to be saved, the key is the configuration name and the value is a Config
        object.
    @param fwrite: file
        A file writer type object.
    @param maxwidth: integer
        The maximum width to use for the description comments.
    '''
    assert isinstance(configurations, dict), 'Invalid configurations %s' % configurations
    assert fwrite, 'No writer provided'
    assert isinstance(maxwidth, int), 'Invalid maximum width %s' % maxwidth

    import yaml
    write = StringIO()
    groups = {config.group for config in configurations.values()}
    for group in sorted(groups):
        fwrite.write('\n# %s %r\n' % ('-' * maxwidth, group))
        configByGroup = [(config.name, name) for name, config in configurations.items() if config.group == group]
        configByGroup.sort(key=lambda pack: pack[0])
        for _fullName, name in configByGroup:
            config = configurations[name]
            assert isinstance(config, Config), 'Invalid configuration %s' % config
            if config.description:
                fwrite.write('\n### %s\n' % '\n### '.join(line for line in REGEX_SPLIT.split(config.description)
                                                        if line.strip()))
            
            if config.isCommented:
                yaml.dump({name: config.value}, write, default_flow_style=False)
                write.seek(0)
                for line in write.readlines(): fwrite.write('#%s' % line)
                write.seek(0)
                write.truncate()
            else:
                yaml.dump({name: config.value}, fwrite, default_flow_style=False)

def load(fread):
    '''
    Loads the configurations from the provided read file handler.
    
    @param fread: file
        A file read type object.
    @return: dictionary{string, object}
        The configuration dictionary.
    '''
    assert fread, 'No reader provided'

    import yaml
    config = yaml.load(fread)
    if config is None: config = {}
    assert isinstance(config, dict), 'Invalid configuration loaded %s' % config
    return config

# --------------------------------------------------------------------

class Config:
    '''
    Class for providing a configuration data.
    '''
    __slots__ = ('name', 'value', 'group', 'description', 'isCommented')

    def __init__(self, name, value, group=None, description=None, isCommented=False):
        '''
        Construct the configuration.
        
        @param name: string
            The full name of the configuration.
        @param value: object|None
            The configuration value.
        @param group: string
            The configuration group.
        @param description: string
            The configuration description.
        @param isCommented: boolean
            Flag indicating that the value should be commented.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert not group or isinstance(group, str), 'Invalid group %s' % group
        assert not description or isinstance(description, str), 'Invalid description %s' % description
        self.name = name
        self.value = value
        self.group = group
        self.description = description
        self.isCommented = isCommented
