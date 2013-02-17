'''
Created on Feb 12, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the merging support functions.
'''

from .context import Object
from .spec import AssemblyError, IAttribute, ContextMetaClass, AttrError, \
    IProcessor
from collections import Iterable, deque

# --------------------------------------------------------------------

class Merger:
    '''
    Merger context class used by processors for data.
    '''
    __slots__ = ('_name', '_parent', '_contexts', '_attributes', '_track', '_calls', '_processors', '_branches')
    
    def __init__(self, name, contexts):
        '''
        Construct the merger instance.
        
        @param name: string
            The merger name.
        @param contexts: dictionary{string, ContextMetaClass}
            The contexts that need to be solved in this merger context.
        @param track: boolean
            Flag indicating that the attributes should be tracked for activity.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
        if __debug__:
            for contextName, clazz in contexts.items():
                assert isinstance(contextName, str), 'Invalid context name %s' % contextName
                assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        
        self._name = name
        self._parent = None
        self._contexts = contexts
        self._attributes = {}
        
        self._calls = []
        self._processors = deque()
        self._branches = []
    
    def branch(self, name):
        '''
        Create a new merger branch.
        
        @param name: string
            The branch merger name.
        @return: Merger
            The branch merger.
        '''
        branch = Merger(name, self._contexts)
        branch._parent = self
        self._branches.append(branch)
        return branch
     
    def branchExtract(self, name, contexts):
        '''
        Create a new merger branch with the provided contexts and extracts the attributes for those context from this merger.
        
        @param contexts: dictionary{string, ContextMetaClass}
            The contexts of the new branch.
        @param name: string
            The extracted branch merger name.
        '''
        assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
        branch = Merger(name, contexts)
        branch._parent = self
        for contextName in contexts:
            for key, attribute in self._attributes.items():
                nameContext, _nameAttribute = key
                if nameContext == contextName: branch._attributes[key] = attribute
        self._branches.append(branch)
        return branch
    
    def branchNew(self, name, contexts):
        '''
        Creates a new merger branch that is known to this merger (mostly for reporting purposes).
        
        @param name: string
            The merger name.
        @param contexts: dictionary{string, ContextMetaClass}
            The contexts that need to be solved in the new merger context.
        @return: Merger
            The new merger.
        '''
        branch = Merger(name, contexts)
        branch._parent = self
        self._branches.append(branch)
        return branch
    
    # ----------------------------------------------------------------
            
    def processNow(self, processors):
        '''
        Process with this merger the provided processors.
        
        @param processors: Iterable(IProcessor)
            The processors to be executed with this merger.
        @return: self
            This merger for chaining purposes.
        '''
        assert isinstance(processors, Iterable), 'Invalid processors %s' % processors
        for processor in processors:
            assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
            processor.register(self)
        return self
    
    def processNext(self):
        '''
        Process the next cycle of processors that are found in the merger.
         If the merger is not resolved then it will be resolved automatically.
        
        @return: boolean
            True if there has been something to process, False otherwise. 
        '''        
        processed = False
        for branch in self._branches:
            assert isinstance(branch, Merger), 'Invalid branch %s' % branch
            processed |= branch.processNext()
        
        if self._processors:
            processed = True
            processors = list(self._processors)
            self._processors.clear()
            self.processNow(processors)
        return processed
    
    def processAllNext(self):
        '''
        Process all the internal processors in cycles. At every cycle the attributes need to be valid.
        
        @return: self
            This merger for chaining purposes.
        '''
        processed = True
        while processed:
            processed = self.processNext()
        return self
            
    # ----------------------------------------------------------------
    
    def addCall(self, call):
        '''
        Adds a new call to the merger.
        
        @param call: callable
            The call to add to the merger.
        @return: self
            This merger for chaining purposes.
        '''
        assert callable(call), 'Invalid call %s' % call
        self._calls.append(call)
        return self
    
    def addOnNext(self, processor):
        '''
        Adds the processor to be executed on the next cycle.
        
        @param processor: IProcessor
            The processor to be executed on the next cycle.
        @return: self
            This merger for chaining purposes.
        '''
        assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
        self._processors.append(processor)
        return self

    # ----------------------------------------------------------------
       
    def merge(self, contexts):
        '''
        Merges the merger attributes with the provided contexts.
        
        @param contexts: dictionary{string, ContextMetaClass)
            The contexts to be merged.
        @return: self
            This merger for chaining purposes.
        '''
        try: merge(self._attributes, iterate(contexts))
        except AttrError: raise AssemblyError('A problem occurred while merging on %s' % self)
        return self
    
    def mergeWithParent(self):
        '''
        Merges the parent merger attributes with this merger attributes. The merged attributes will be in this merger.
        
        @return: self
            This merger for chaining purposes.
        '''
        assert self._parent, 'There is no parent for this merger'
        parent = self._parent
        assert isinstance(parent, Merger), 'Invalid parent merger %s' % parent
        attributes = dict(self._attributes)
        self._attributes.clear()
        self._attributes.update(parent._attributes)
        try: merge(self._attributes, attributes)
        except AttrError: raise AssemblyError('A problem occurred while merging with parent for %s' % self)
        return self
    
    def mergeOnParent(self):
        '''
        Merges the parent merger attributes with this merger attributes. The merged attributes will be in the parent merger.
        
        @return: self
            This merger for chaining purposes.
        '''
        assert self._parent, 'There is no parent for this merger'
        parent = self._parent
        assert isinstance(parent, Merger), 'Invalid parent merger %s' % parent
        try: merge(parent._attributes, self._attributes)
        except AttrError: raise AssemblyError('A problem occurred while merging on parent for %s' % self)
        return self
    
    def solve(self, contexts):
        '''
        Solves the merger attributes with the provided contexts.
        
        @param contexts: dictionary{string, ContextMetaClass)
            The contexts to be solved.
        @return: self
            This merger for chaining purposes.
        '''
        solve(self._attributes, iterate(contexts))
        return self
    
    def solveOnParent(self):
        '''
        Solves this merger into the parent merger.The solved attributes will be in the parent merger.
        
        @return: self
            This merger for chaining purposes.
        '''
        assert self._parent, 'There is no parent for this merger'
        parent = self._parent
        assert isinstance(parent, Merger), 'Invalid parent merger %s' % parent
        solve(parent._attributes, self._attributes)
        return self
    
    def resolve(self):
        '''
        Resolve the merger contexts with the attributes.
        
        @return: self
            This merger for chaining purposes.
        '''
        solve(self._attributes, iterate(self._contexts))
        return self
    
    # ----------------------------------------------------------------
    
    def calls(self):
        '''
        Provides the merger calls.
        
        @type calls: Iterator(Callable)
            The calls of the merger.
        '''
        return iter(self._calls)
        
    def createContexts(self):
        '''
        Creates the object contexts for this merger.
        
        @return: dictionary{string, ContextMetaClass)
            The resolved contexts.
        '''
        for key, attribute in self._attributes.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            if not attribute.isCreatable():
                raise AttrError('The %s.%s unsolved for %s, on %s' % (key + (attribute, self)))
        
        namespaces = {}
        for key, attribute in self._attributes.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            nameContext, nameAttribute = key
    
            namespace = namespaces.get(nameContext)
            if namespace is None: namespace = namespaces[nameContext] = dict(__module__=__name__)
            namespace[nameAttribute] = attribute
    
        return {name: type('Object$%s%s' % (name[0].upper(), name[1:]), (Object,), namespace)
                for name, namespace in namespaces.items()}
        
    # ----------------------------------------------------------------
    
    def represent(self):
        '''
        Represent the merger.
        
        @return: list[string]
            The lines that compose the representation.
        '''
        repr = ['%s, with contexts:' % self._name]
        for name, context in self._contexts.items():
            repr.append('\t%s: %s' % (name, context))
        repr.append(', with attributes %s' % ', '.join('%s.%s' % key for key in self._attributes))
        return repr
    
    def representStructue(self):
        '''
        Lists the structure of this merger.
        
        @return: list[string]
            The lines that compose the listing.
        '''
        repr = self.represent()
             
        if self._parent:
            parent = self._parent
            assert isinstance(parent, Merger), 'Invalid parent %s' % parent
            repr.append(', with parent:')
            repr.extend('\t%s' % line for line in parent.represent())
        else: repr.append(', has no parent')
       
        if self._branches:
            repr.append(', with branches:')
            for branch in self._branches:
                assert isinstance(branch, Merger), 'Invalid branch %s' % branch
                repr.extend('\t%s' % line for line in branch.represent())
        else: repr.append(', has no branches')
        
        return repr
    
    def report(self):
        '''
        Creates the report for this merger.
        
        @return: list[string]
            The lines that compose the report.
        '''
        #TODO: make a better report 
        report = ['Report for %s' % self._name]
        for key, attribute in self._attributes.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            if not attribute.isUsed():
                line = '\tNever used %s.%s for %s' % (key + (attribute,))
                report.append(line.strip())
                
        for branch in self._branches:
            assert isinstance(branch, Merger)
            report.append('')
            report.extend('\t%s' % line for line in branch.report())
            
        return report
            
    def __str__(self):
        return '%s for %s' % (self.__class__.__name__, '\n'.join(self.representStructue()))

# --------------------------------------------------------------------

def iterate(contexts):
    '''
    Iterate the attributes of the provided contexts.
    
    @param contexts: dictionary{string, ContextMetaClass)
        The contexts to have the attributes iterated.
    @return: Iterable(tuple(string, string), IAttribute)
        The attributes iterator.
    '''
    assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
    for nameContext, context in contexts.items():
        assert isinstance(nameContext, str), 'Invalid context name %s' % nameContext
        assert isinstance(context, ContextMetaClass), 'Invalid context class %s' % context

        for nameAttribute, attribute in context.__attributes__.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            yield (nameContext, nameAttribute), attribute

def merge(main, other):
    '''
    Merges into the provided attributes the other attributes.
    
    @param main: dictionary{tuple(string, string), IAttribute}
        The main attributes to merge to.
    @param other: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. This attributes will be merged into the main attributes.
    @return: dictionary{tuple(string, string), IAttribute}
        Provides the main dictionary.
    '''
    assert isinstance(main, dict), 'Invalid main attributes %s' % main
    if isinstance(other, dict): other = other.items()
    assert isinstance(other, Iterable), 'Invalid other attributes %s' % other

    for key, attribute in other:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        assert isinstance(key, tuple), 'Invalid key %s' % key

        attr = main.get(key)
        if attr is None: main[key] = attribute
        else:
            assert isinstance(attr, IAttribute), 'Invalid attribute %s' % attr 
            main[key] = attr.merge(attribute)
            
    return main

def solve(main, other):
    '''
    Solves into the provided attributes the other attributes.
    
    @param main: dictionary{tuple(string, string), IAttribute}
        The main attributes to solve to.
    @param other: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. This attributes will be merged into the main attributes.
    @return: dictionary{tuple(string, string), IAttribute}
        Provides the main dictionary.
    '''
    assert isinstance(main, dict), 'Invalid main attributes %s' % main
    if isinstance(other, dict): other = other.items()
    assert isinstance(other, Iterable), 'Invalid other attributes %s' % other

    for key, attribute in other:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        assert isinstance(key, tuple), 'Invalid key %s' % key
        
        attr = main.get(key)
        if attr is None: main[key] = attribute
        else: main[key] = attribute.solve(attr)
    return main
