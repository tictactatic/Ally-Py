'''
Created on Mar 15, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path support.
'''

from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.container.ioc import injected
from ally.core.spec.resources import Path
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.support.core.util_resources import findGetModel, findGetAllAccessible, \
    pathLongName
from ally.api.type import Iter
from ally.api.operator.container import Model
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
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    pathMain = defines(Path, doc='''
    @rtype: Path
    The main path of the model.
    ''')
    pathsModels = defines(dict, doc='''
    @rtype: dictionary{TypeModel: Path}
    The paths of the model, this paths are linked with the main path.
    ''')
    pathsAccesible = defines(dict, doc='''
    @rtype: dictionary{string: Path}
    The accessible paths, this paths are linked with the main path.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(Path)
    
# --------------------------------------------------------------------

@injected
class PathSupport(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the path support.
    '''
        
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
        
        if isinstance(objType, TypeModel): modelType = objType
        elif isinstance(objType, TypeModelProperty):
            assert isinstance(objType, TypeModelProperty)
            modelType = objType.parent
        else: return  # Cannot use the object type, moving along
        
        assert isinstance(support.path, Path), 'Invalid path %s' % support.path
        
        if support.pathsModels is None: support.pathsModels = {}
        if support.pathsAccesible is None: support.pathsAccesible = OrderedDict()
        
        pathModel = findGetModel(support.path, modelType)
        if pathModel is None: return  # No model path available
        support.pathMain = pathModel
        
        assert isinstance(modelType, TypeModel)
        assert isinstance(modelType.container, Model)
        for valueType in modelType.container.properties.values():
            if isinstance(valueType, TypeModel):
                pathProp = findGetModel(pathModel, valueType)
                if pathProp: support.pathsModels[valueType] = pathProp
                
        # TODO: Make sure when placing the accessible paths that there isn't already an accessible path
        # that already returns the inherited model see the example for MetaData and ImageData in relation
        # with MetaInfo and ImageInfo
        for path in findGetAllAccessible(pathModel):
            pathName = pathLongName(path)
            if pathName not in support.pathsAccesible: support.pathsAccesible[pathName] = path
        # These paths will get updated in the encode model when the data model path is updated
        # because they are extended from the base path.
        for parentType in modelType.parents():
            parentPath = findGetModel(pathModel, parentType)
            if parentPath:
                for path in findGetAllAccessible(parentPath):
                    pathName = pathLongName(path)
                    if pathName not in support.pathsAccesible: support.pathsAccesible[pathName] = path
