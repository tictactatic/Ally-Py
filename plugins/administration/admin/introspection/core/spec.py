'''
Created on Oct 1, 2013

@package: administration
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides centralized function to dictate the Id construct for introspection models. 
'''

from ally.api.operator.type import TypeModel, TypeProperty

# --------------------------------------------------------------------

def modelId(typeModel):
    '''
    Provides the model id for the provided type model.
    
    @param typeModel: TypeModel
        The model type to construct the id based on.
    @return: string
        The id of the model type.
    '''
    assert isinstance(typeModel, TypeModel), 'Invalid model type %s' % typeModel
    return '%s.%s' % (typeModel.clazz.__module__, typeModel.clazz.__name__)

def propertyId(typeProperty):
    '''
    Provides the property id for the provided type property.
    
    @param typeProperty: TypeProperty
        The property type to construct the id based on.
    @return: integer
        The id of the property type.
    '''
    assert isinstance(typeProperty, TypeProperty), 'Invalid property type %s' % typeProperty
    return '%s.%s' % (modelId(typeProperty.parent), typeProperty.name) 
