'''
Created on Jan 12, 2012

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides support functions for the container.
'''

from ..support.util_sys import callerLocals, callerGlobals
from ._impl._aop import AOPResources
from ._impl._assembly import Assembly
from ._impl._call import CallEntity, CallConfig, CallEventControlled
from ._impl._entity import Wiring, WireConfig, Advent, Event
from ._impl._setup import register, SetupConfig, setupsOf, setupFirstOf, \
    SetupStart, SetupEventControlled
from ._impl._support import SetupEntityListen, SetupEntityListenAfterBinding, \
    classesFrom, SetupEntityWire, SetupEntityCreate
from .error import ConfigError, SetupError
from .event import ITrigger
from .impl.config import Config
from .impl.priority import sortByPriorities
from .ioc import PRIORITY_LAST
from collections import Iterable
from copy import deepcopy
from functools import partial
from inspect import isclass, ismodule, getsource, isfunction, ismethod

# --------------------------------------------------------------------

def nameEntity(clazz, module=None):
    '''
    Creates the setup names to be used setup modules based on a setup class and name.
    
    @param clazz: class
        The class that is considered the entity.
    @param name: string|function
        The name of the property or function to create a name for.
    @param module: string|module|None
        The group or setup module to consider as setup container, if not provided the calling module is considered.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    if module:
        if ismodule(module): module = module.__name__
        assert isinstance(module, str), 'Invalid module %s' % module
    
    try: types, name = clazz.__ally_setup__
    except AttributeError: types = name = None
    if name is None:
        if types is None: name = clazz.__name__
        else:
            assert isclass(types[0]), 'Invalid class %s' % types[0]
            name = types[0].__name__
    
    if module: return '%s.%s' % (module, name)
    return name

def nameInEntity(clazz, name, module=None):
    '''
    Creates the setup names to be used setup modules based on a setup class and name.
    
    @param clazz: class
        The class that is considered the entity.
    @param name: string|function
        The name of the property or function to create a name for.
    @param module: string|module|None
        The group or setup module to consider as setup container, if not provided the calling module is considered.
    '''
    if isfunction(name) or ismethod(name): name = name.__name__
    assert isinstance(name, str), 'Invalid name %s' % name
    
    return '%s.%s' % (nameEntity(clazz, module), name)

# --------------------------------------------------------------------

def callEntityEvent(name, nameEvent, assembly=None):
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open!
    Calls a inner entity event.
    
    @param name: string
        The setup name of the entity having the event function.
    @param clazz: class
        The class of the entity to call the event for.
    @param nameEvent: string|function
        The name of the event function.
    @param assembly: Assembly|None
        The assembly to find the entity in, if None the current assembly will be considered.
    '''
    assert isinstance(name, str), 'Invalid setup name %s' % name
    if isfunction(nameEvent) or ismethod(nameEvent): nameEvent = nameEvent.__name__
    assert isinstance(nameEvent, str), 'Invalid event name %s' % nameEvent
    
    assembly = assembly or Assembly.current()
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
    
    Assembly.stack.append(assembly)
    entity = assembly.processForName(name)
    try: return getattr(entity, nameEvent)()
    except AttributeError: raise SetupError('Invalid call name \'%s\' for entity %s' % (name, entity))
    finally: Assembly.stack.pop()

# --------------------------------------------------------------------

def setup(*types, name=None):
    '''
    Decorate a IMPL class with the info about required API class and optional a name
    
    @param types: arguments[class]
        The type(s) of the correspondent API. If no type is provided then the decorated class is considered as the return type.
    @param name: string
        The name associated to created IOC object
    '''
    assert name is None or isinstance(name, str), 'Expected a string name instead of %s ' % name
    if __debug__:
        for clazz in types: assert isclass(clazz), 'Invalid api class %s' % clazz

    def decorator(clazz):
        setattr(clazz, '__ally_setup__', (types if types else (clazz,), name))
        return clazz

    return decorator

def notCreated():
    '''
    Function that just raises a SetupError for when an expected entity created by 'createEntitySetup' is not present. 
    '''
    raise SetupError('No entity created for this name by \'createEntitySetup\' function')

def createEntitySetup(*classes, module=None, nameEntity=nameEntity, nameInEntity=nameInEntity):
    '''
    For impl classes create the setup functions for the associated API classes. The name of the setup functions that will be generated
    are formed based on the provided formatter. To create a setup function a class from the impl classes has to inherit the api class.
    
    @param classes: arguments(string|class|module|AOPClasses)
        The classes to be considered the implementations for the APIs.
    @param module: module|None
        If the setup module is not provided than the calling module will be considered.
    @param nameEntity: callable like @see: nameEntity
        The formatter to use in creating the entity setup function name.
    @param nameInEntity: callable like @see: nameInEntity
        The formatter to use in creating the setup function names based on entity properties.
    '''
    if module:
        assert ismodule(module), 'Invalid setup module %s' % module
        registry = module.__dict__
        group = module.__name__
    else:
        registry = callerLocals()
        assert '__name__' in registry, 'The create entity call needs to be made directly from the setup module'
        group = registry['__name__']
    assert callable(nameEntity), 'Invalid entity name formatter %s' % nameEntity
    
    wireClasses = []
    for clazz in classesFrom(classes):
        try: types, _name = clazz.__ally_setup__
        except AttributeError: continue
        
        wireClasses.append(clazz)
        setupCreate = register(SetupEntityCreate(clazz, types, name=nameEntity(clazz, group), group=group), registry)
        registry[nameEntity(clazz)] = setupCreate

    wireEntities(*wireClasses, module=module, nameInEntity=nameInEntity)
    eventEntities(*wireClasses, module=module, nameInEntity=nameInEntity)

def wireEntities(*classes, module=None, nameInEntity=nameInEntity):
    '''
    Creates entity wiring setups for the provided classes. The wiring setups consists of configurations found in the
    provided classes that will be published in the setup module.
    
    @param classes: arguments(string|class|module|AOPClasses)
        The classes to be wired.
    @param module: module|None
        If the setup module is not provided than the calling module will be considered.
    @param nameInEntity: callable like @see: nameInEntity
        The formatter to use in creating the setup function names based on entity properties.
    '''
    if module:
        assert ismodule(module), 'Invalid setup module %s' % module
        registry = module.__dict__
        group = module.__name__
    else:
        registry = callerLocals()
        assert '__name__' in registry, 'The create wiring call needs to be made directly from the setup module'
        group = registry['__name__']
    assert callable(nameInEntity), 'Invalid name in entity formatter %s' % nameInEntity
    
    def processConfig(clazz, wconfig):
        assert isclass(clazz), 'Invalid class %s' % clazz
        assert isinstance(wconfig, WireConfig), 'Invalid wire configuration %s' % wconfig
        value = clazz.__dict__.get(wconfig.name, None)
        if value and not isclass(value): return deepcopy(value)
        if wconfig.hasValue: return deepcopy(wconfig.value)
        raise ConfigError('A configuration value is required for \'%s\' in class %s' % (wconfig.name, clazz.__name__))

    wirings = {}
    for clazz in classesFrom(classes):
        wiring = Wiring.wiringOf(clazz)
        if wiring:
            wirings[clazz] = wiring
            assert isinstance(wiring, Wiring)
            for wconfig in wiring.configurations:
                assert isinstance(wconfig, WireConfig)
                name = nameInEntity(clazz, wconfig.name, group)
                for setup in setupsOf(registry, SetupConfig):
                    assert isinstance(setup, SetupConfig)
                    if setup.name == name: break
                else:
                    configCall = partial(processConfig, clazz, wconfig)
                    configCall.__doc__ = wconfig.description
                    if wconfig.type is not None: types = (wconfig.type,)
                    else: types = ()
                    register(SetupConfig(configCall, types=types, name=name, group=group), registry)
    if wirings:
        wire = setupFirstOf(registry, SetupEntityWire)
        if not wire: wire = register(SetupEntityWire(group), registry)
        assert isinstance(wire, SetupEntityWire)
        wire.update(wirings, nameInEntity)

def eventEntities(*classes, module=None, nameInEntity=nameInEntity):
    '''
    Creates entity event setups for the provided classes. The event setups consists of configurations found in the
    provided classes that will be published in the setup module.
    !!! Currently this works only with 'createEntitySetup'.
    
    @param classes: arguments(string|class|module|AOPClasses)
        The classes to be processed for events.
    @param module: module|None
        If the setup module is not provided than the calling module will be considered.
    @param nameInEntity: callable like @see: nameInEntity
        The formatter to use in creating the setup function names based on event calls.
    '''
    if module:
        assert ismodule(module), 'Invalid setup module %s' % module
        registry = module.__dict__
        group = module.__name__
    else:
        registry = callerLocals()
        assert '__name__' in registry, 'The event entities call needs to be made directly from the setup module'
        group = registry['__name__']
    assert callable(nameInEntity), 'Invalid name in entity formatter %s' % nameInEntity
    
    for clazz in classesFrom(classes):
        advent = Advent.adventOf(clazz)
        if advent:
            assert isinstance(advent, Advent)
            for event in advent.events:
                assert isinstance(event, Event)
                name = nameInEntity(clazz, event.name, group)
                eventCall = partial(callEntityEvent, name, event.name)
                register(SetupEventControlled(eventCall, event.priority, event.triggers, name=name, group=group), registry)

# --------------------------------------------------------------------

def listenToEntities(*classes, listeners=None, beforeBinding=True, module=None, all=False):
    '''
    Listens for entities defined in the provided module that are of the provided classes. The listening is done at the 
    moment of the entity creation so the listen is not dependent of the declared entity return type.
    
    @param classes: arguments(string|class|module|AOPClasses)
        The classes to listen to, this classes can be either the same class or a super class of the instances generated
        by the entity setup functions.
    @param listeners: None|Callable|list[Callable]|tuple(Callable)
        The listeners to be invoked. The listeners Callable's will take one argument that is the instance.
    @param module: module|dictionary{string:object}|None
        If the setup module is not provided than the calling module will be considered as the registry for the setup.
    @param all: boolean
        Flag indicating that the listening should be performed on all assembly.
    @param beforeBinding: boolean
        Flag indicating that the listening should be performed before any binding occurs (True) or after the
        bindings (False).
    '''
    if not listeners: listeners = []
    elif not isinstance(listeners, (list, tuple)): listeners = [listeners]
    assert isinstance(listeners, (list, tuple)), 'Invalid listeners %s' % listeners
    assert isinstance(beforeBinding, bool), 'Invalid before binding flag %s' % beforeBinding
    assert isinstance(all, bool), 'Invalid all flag %s' % all
    if not module:
        registry = callerLocals()
        assert '__name__' in registry, 'The listen to entities call needs to be made directly from the setup module'
        if all: group = None
        else: group = registry['__name__']
    elif ismodule(module):
        registry = module.__dict__
        if all: group = None
        else: group = module.__name__
    else:
        assert isinstance(module, dict), 'Invalid setup module %s' % module
        assert '__name__' in module, 'The provided registry dictionary has no __name__'
        registry = module
        if all: group = None
        else: group = module['__name__']

    if beforeBinding: setup = SetupEntityListen(group, classesFrom(classes), listeners)
    else: setup = SetupEntityListenAfterBinding(group, classesFrom(classes), listeners)
    register(setup, registry)

def loadAllEntities(*classes, module=None):
    '''
    Loads all entities that have the type in the provided classes.
    
    @param classes: arguments(string|class|module|AOPClasses)
        The classes to have the entities loaded for.
    @param module: module|None
        If the setup module is not provided than the calling module will be considered.
    @return: Setup
        The setup start that loads all the entities, the return value can be used for after and before events.
    '''
    def loadAll(prefix, classes):
        for clazz in classes:
            for name, call in Assembly.current().calls.items():
                if name.startswith(prefix) and isinstance(call, CallEntity) and call.isOf(clazz): Assembly.process(name)

    if module:
        assert ismodule(module), 'Invalid setup module %s' % module
        registry = module.__dict__
        group = module.__name__
    else:
        registry = callerLocals()
        assert '__name__' in registry, 'The load all entities call needs to be made directly from the setup module'
        group = registry['__name__']

    loader = partial(loadAll, group + '.', classesFrom(classes))
    return register(SetupStart(loader, PRIORITY_LAST, name='loader_%s' % id(loader)), registry)

def include(module, inModule=None):
    '''
    By including the provided module all the setup functions from the the included module are added as belonging to the
    including module, is just like defining the setup functions again in the including module.
    
    @param module: module
        The module to be included.
    @param inModule: module|None
        If the setup module is not provided than the calling module will be considered.
    '''
    assert ismodule(module), 'Invalid module %s' % module

    if inModule:
        assert ismodule(inModule), 'Invalid setup module %s' % inModule
        registry = inModule.__dict__
    else: registry = callerLocals()
    exec(compile(getsource(module), registry['__file__'], 'exec'), registry)

# --------------------------------------------------------------------
# Functions available in setup functions calls.

def entities():
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open!
    Provides all the entities references found in the current assembly wrapped in a AOP class.
    
    @return: AOP
        The resource AOP.
    '''
    return AOPResources({name:name for name, call in Assembly.current().calls.items() if isinstance(call, CallEntity)})

def entitiesLocal():
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open!
    Provides all the entities references for the module from where the call is made found in the current assembly.
    
    @return: AOP
        The resource AOP.
    '''
    registry = callerGlobals()
    assert '__name__' in registry, 'The entities local call needs to be made from a setup module function'
    rsc = AOPResources({name:name for name, call in Assembly.current().calls.items() if isinstance(call, CallEntity)})
    rsc.filter(registry['__name__'] + '.**')
    return rsc

def entitiesFor(clazz, assembly=None):
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open! 
    Provides the entities for the provided class (only if the setup function exposes a return type that is either the
    provided class or a super class) found in the current assembly.
    
    @param clazz: class
        The class to find the entities for.
    @param assembly: Assembly|None
        The assembly to find the entities in, if None the current assembly will be considered.
    @return: list[object]
        The instances for the provided class.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assembly = assembly or Assembly.current()
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly

    entities = (name for name, call in assembly.calls.items() if isinstance(call, CallEntity) and call.isOf(clazz))

    Assembly.stack.append(assembly)
    try: return [assembly.processForName(name) for name in entities]
    finally: Assembly.stack.pop()

def entityFor(clazz, name=None, group=None, assembly=None):
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open!
    Provides the entity for the provided class (only if the setup function exposes a return type that is either the
    provided class or a super class) found in the current assembly.
    
    @param clazz: class
        The class to find the entity for.
    @param name: string|None
        The optional name for the entity to be found, this will be considered if there are multiple entities for the class.
    @param group: string|module
        The group or setup module to consider as setup.
    @param assembly: Assembly|None
        The assembly to find the entity in, if None the current assembly will be considered.
    @return: object
        The instance for the provided class.
    @raise SetupError: In case there is no entity for the required class or there are to many.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assert name is None or isinstance(name, str), 'Invalid name %s' % name
    if group:
        if ismodule(group): group = group.__name__
        assert isinstance(group, str), 'Invalid group %s' % group
    assembly = assembly or Assembly.current()
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly

    entities = [nameCall for nameCall, call in assembly.calls.items() if isinstance(call, CallEntity) and call.isOf(clazz)]
    if not entities:
        raise SetupError('There is no entity setup function having a return type of class or subclass %s' % clazz)
    if len(entities) > 1:
        if group:
            if not group.endswith('.'): pgroup = '%s.' % group
            else: pgroup = group
            entities = [fname for fname in entities if fname.startswith(pgroup)]
        
        if name:
            if not name.startswith('.'): pname = '.%s' % name
            else: pname = name
            entities = [fname for fname in entities if fname == name or fname.endswith(pname)]
    
            if not entities:
                raise SetupError('No setup functions having a return type of class or subclass %s and name resembling %s' % 
                                 (clazz, ('%s.*.%s' % (group, name) if group else name)))
            if len(entities) > 1:
                raise SetupError('To many entities setup functions %s having a return type of class or subclass %s '
                        'and name resembling %s' % (', '.join(entities), clazz, ('%s.*.%s' % (group, name) if group else name)))
        else:
            raise SetupError('To many entities setup functions %s having a return type of class or subclass %s' % 
                             (', '.join(entities), clazz))

    Assembly.stack.append(assembly)
    try: return assembly.processForName(entities[0])
    finally: Assembly.stack.pop()
    
# --------------------------------------------------------------------

def eventsFor(*triggers, source=None):
    '''
    !Attention this function is only available in an open assembly if the source is not provided @see: ioc.open!
    Provides all the events for the assembly that match the provided event.
    
    @param triggers: arguments[object]
        The triggers to fetch for.
    @param source: Assembly|Iterable(tuple(string, callable))|None
        The source to provide the events for, it can be an assembly in which case the assembly calls are used as the source
        or it can be an iterable providing tuples of name and call. If None then the current assembly calls are used.
    @return: Iterable(tuple(Callable, string, ITrigger))
        An iterator that yields tuples having on the first position the call will return True for a successful event execution,
        False otherwise, on the second position the event name and on the last position the trigger.
    '''
    assert triggers, 'At least one trigger is required'
    if source is None: source = Assembly.current()
    if isinstance(source, Assembly):
        assembly = source
        source = source.calls.items()
    else: assembly = None
    assert isinstance(source, Iterable), 'Invalid source %s' % source
    
    calls = []
    for name, call in source:
        if not isinstance(call, CallEventControlled): continue
        assert isinstance(call, CallEventControlled)
        if assembly is not None and call.assembly != assembly: continue
        for trigger in call.triggers:
            assert isinstance(trigger, ITrigger), 'Invalid trigger %s' % trigger
            if trigger.isTriggered(triggers):
                calls.append((call, name, trigger))
    sortByPriorities(calls, priority=lambda item: item[0].priority, reverse=True)
    return calls

# --------------------------------------------------------------------

def force(setup, value, assembly=None):
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open!
    Forces a configuration setup to have the provided value. This method should be called in a @ioc.before event that
    targets the forced value configuration.
    
    @param setup: SetupConfig
        The setup to force the value on.
    @param value: object
        The value to be forced, needs to be compatible with the configuration setup.
    @param assembly: Assembly|None
        The assembly to find the configuration in, if None the current assembly will be considered.
    '''
    assert isinstance(setup, SetupConfig), 'Invalid setup %s' % setup
    assembly = assembly or Assembly.current()
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
    
    Assembly.stack.append(assembly)
    try:
        call = assembly.fetchForName(setup.name)
        assert isinstance(call, CallConfig), 'Invalid call %s' % call
        call.value = value
    finally: Assembly.stack.pop()
    
def persist(setup, value, assembly=None):
    '''
    !Attention this function is only available in an open assembly if the assembly is not provided @see: ioc.open!
    Persists a configuration setup to have the provided value but only in saving the configuration file.
    
    @param setup: SetupConfig
        The setup to persist the value on.
    @param value: object
        The value to be forced, needs to be compatible with the configuration setup.
    @param assembly: Assembly|None
        The assembly to find the configuration in, if None the current assembly will be considered.
    '''
    assert isinstance(setup, SetupConfig), 'Invalid setup %s' % setup
    assembly = assembly or Assembly.current()
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
    
    config = assembly.configurations.get(setup.name)
    assert isinstance(config, Config), 'Invalid configuration %s for the assembly' % setup.name
    config.value = value
    
