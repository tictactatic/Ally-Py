'''
Created on Mar 15, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path support.
'''

from ally.api.operator.container import Model
from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.api.type import Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Path, Node, Invoker
from ally.core.spec.transform.encoder import IEncoder
from ally.design.cache import CacheWeak
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.support.core.util_resources import findGetModel, findGetAllAccessible, \
    pathLongName, findEntryModel, findEntries
from collections import OrderedDict

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Required
    objType = requires(object)
    
class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    pathModel = defines(Path, doc='''
    @rtype: Path
    The path of the encoded model.
    ''')
    pathsProperties = defines(dict, doc='''
    @rtype: dictionary{TypeModelProperty: Path}
    The paths of the model properties, this paths need to be updated by the encoder,
    this paths are linked with the model path.
    ''')
    pathsAccesible = defines(dict, doc='''
    @rtype: dictionary{string: Path}
    The accessible paths, this paths are linked with the model path.
    ''')
    updatePaths = defines(dict, doc='''
    @rtype: dictionary{Type: Path}
    The paths to be updated based on type object.
    ''')
    hideProperties = definesIf(bool, doc='''
    @rtype: boolean
    Flag indicating that the properties should be rendered or not.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(Path)
    
class CreateItem(Create):
    '''
    The create item encoder context.
    '''
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)

class SupportItem(Context):
    '''
    The encoder item support context.
    '''
    # ---------------------------------------------------------------- Required
    updatePaths = requires(dict)
    
# --------------------------------------------------------------------

@injected
class PathSupport(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the path support.
    '''
    
    nameMarkedList = '%sList'
    # The name to use for rendering lists of models, contains the '%s' mark where to place the item name.
    
    def __init__(self):
        assert isinstance(self.nameMarkedList, str), 'Invalid name list %s' % self.nameMarkedList
        super().__init__()
        
    def process(self, create:Create, support:Support, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Populates the path support data.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        objType = create.objType
        if isinstance(objType, Iter):
            assert isinstance(objType, Iter)
            objType = objType.itemType
            inCollection = True
        else: inCollection = False
        
        if isinstance(objType, TypeModel):
            modelType = objType
            propType = None
        elif isinstance(objType, TypeModelProperty):
            assert isinstance(objType, TypeModelProperty)
            modelType = objType.parent
            propType = objType
        else: return  # Cannot use the object type, moving along
        
        assert isinstance(support.path, Path), 'Invalid path %s' % support.path
        
        if support.updatePaths is None: support.updatePaths = {}
        if support.pathsProperties is None: support.pathsProperties = {}
        if support.pathsAccesible is None: support.pathsAccesible = OrderedDict()
        
        support.pathModel = findGetModel(support.path, modelType)
        
        if support.pathModel:
            pathAccesible = pathMain = support.pathModel

            if propType:
                assert isinstance(propType, TypeModelProperty)
                if propType.isId():
                    support.updatePaths[propType] = pathMain
                    support.hideProperties = True
                return  # If not a model no other paths are required.
            
            if inCollection:
                support.updatePaths[modelType] = pathMain
                support.hideProperties = True
                # TODO: Gabriel: This is a temporary fix to get the same rendering as before until we refactor the plugins
                # to return only ids.
                return
        else:
            pathMain = findEntryModel(support.path, modelType)
            if pathMain:
                pathAccesible = pathMain
                if inCollection: support.updatePaths[modelType] = pathMain
            else:
                pathAccesible = support.path
        
        if pathMain:
            assert isinstance(modelType, TypeModel)
            assert isinstance(modelType.container, Model)
            for valueType in modelType.container.properties.values():
                if isinstance(valueType, TypeModel):
                    assert isinstance(valueType, TypeModel)
                    pathProp = findGetModel(pathMain, valueType)
                    if pathProp: support.pathsProperties[valueType.propertyTypeId()] = pathProp
                
        # Make sure when placing the accessible paths that there isn't already an accessible path
        # that already returns the inherited model see the example for MetaData and ImageData in relation
        # with MetaInfo and ImageInfo
        accessible = findGetAllAccessible(pathAccesible)
        # These paths will get updated in the encode model when the data model path is updated
        # because they are extended from the base path.
        entries = []
        for entryPath in findEntries(pathAccesible, modelType, True):
            assert isinstance(entryPath, Path)
            # We need to make sure that we don't add the main path to the accessible paths.
            if not pathMain or entryPath.node != pathMain.node: entries.append(entryPath)
        if entries:
            # If we have paths that are available based on the model type we add those to.
            accessible.extend(entries)
            for entryPath in entries: support.updatePaths[modelType] = entryPath
            
        for parentType in modelType.parents():
            parentPath = findGetModel(pathAccesible, parentType)
            if parentPath:
                support.updatePaths[parentType] = parentPath
                accessible.extend(findGetAllAccessible(parentPath))
                        
        for path in accessible:
            assert isinstance(path, Path), 'Invalid path %s' % path
            assert isinstance(path.node, Node), 'Invalid node %s' % path.node
            assert isinstance(path.node.get, Invoker), 'Invalid node get %s' % path.node.get
            pathName = pathLongName(path)
            if isinstance(path.node.get.output, Iter): pathName = self.nameMarkedList % pathName
            if pathName not in support.pathsAccesible:
                support.pathsAccesible[pathName] = path

@injected
class PathUpdaterSupportEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the models paths update when in a collection.
    '''
    
    def __init__(self):
        super().__init__(support=SupportItem)
        
        self._cache = CacheWeak()
        
    def process(self, create:CreateItem, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the update model path encoder.
        '''
        assert isinstance(create, CreateItem), 'Invalid create %s' % create
        
        if create.encoder is None: return 
        # There is no encoder to provide path update for.
        if not isinstance(create.objType, (TypeModel, TypeModelProperty)): return 
        # The type is not for a path updater, nothing to do, just move along
        
        cache = self._cache.key(create.encoder)
        if not cache.has: cache.value = EncoderPathUpdater(create.encoder)
        
        create.encoder = cache.value
        
# --------------------------------------------------------------------

class EncoderPathUpdater(IEncoder):
    '''
    Implementation for a @see: IEncoder that updates the path before encoding .
    '''
    
    def __init__(self, encoder):
        '''
        Construct the path updater.
        '''
        assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
        
        self.encoder = encoder
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(support, SupportItem), 'Invalid support %s' % support
        if support.updatePaths:
            assert isinstance(support.updatePaths, dict), 'Invalid update paths %s' % support.updatePaths
            for objType, path in support.updatePaths.items():
                assert isinstance(path, Path)
                path.update(obj, objType)
        
        self.encoder.render(obj, render, support)
        
    def represent(self, support, obj=None):
        '''
        @see: IEncoder.represent
        '''
        return self.encoder.represent(support, obj)
