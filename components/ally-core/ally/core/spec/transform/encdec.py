'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides encoder decoder specifications. 
'''

from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
import abc

# --------------------------------------------------------------------

class IEncoder(metaclass=abc.ABCMeta):
    '''
    The encoder specification.
    '''
    
    @abc.abstractmethod
    def encode(self, obj, target, support):
        '''
        Renders the value in to the provided renderer.
        
        @param obj: object
            The value object to be encoded.
        @param target: object
            The target to be used to place the encoded value.
        @param support: object
            Support context object containing additional data required for encoding.
        '''

class ISpecifier(metaclass=abc.ABCMeta):
    '''
    The specifications modifier for rendering.
    '''
    
    @abc.abstractmethod
    def populate(self, obj, specifications, support):
        '''
        Populates the rendering specifications before being used by an encoder.
        
        @param obj: object
            The value object to process based on.
        @param specifications: dictionary{string: object}
            The rendering specifications to process.
        @param support: object
            Support context object containing additional data required for processing.
        '''

class IRender(metaclass=abc.ABCMeta):
    '''
    The specification for the renderer of encoded objects.
    '''
    __slots__ = ()

    @abc.abstractclassmethod
    def property(self, name, value, **specifications):
        '''
        Called to signal that a property value has to be rendered.

        @param name: string
            The property name.
        @param value: string|tuple(string)|list[string]|dictionary{string: string}
            The value.
        @param specifications: key arguments
            Additional key arguments specifications dictating the rendering.
        '''

    @abc.abstractclassmethod
    def beginObject(self, name, **specifications):
        '''
        Called to signal that an object has to be rendered.
        
        @param name: string
            The object name.
        @param specifications: key arguments
            Additional key arguments specifications dictating the rendering.
        @return: self
            The same render instance for chaining purposes.
        '''

    @abc.abstractclassmethod
    def beginCollection(self, name, **specifications):
        '''
        Called to signal that a collection of objects has to be rendered.
        
        @param name: string
            The collection name.
        @param specifications: key arguments
            Additional key arguments specifications dictating the rendering.
        @return: self
            The same render instance for chaining purposes.
        '''

    @abc.abstractclassmethod
    def end(self):
        '''
        Called to signal that the current block (object or collection) has ended the rendering.
        '''

# --------------------------------------------------------------------

class IDecoder(metaclass=abc.ABCMeta):
    '''
    The decoder specification.
    '''
    
    @abc.abstractmethod
    def decode(self, path, obj, target, support):
        '''
        Decode the value based on the path in to the provided objects.
        
        @param path: object
            The path describing where the value should be placed.
        @param obj: object
            The value to be placed on the path.
        @param target: object
            The target object to decode in.
        @param support: object
            Support context object containing additional data required for decoding.
        @return: boolean|None
            If True it means that the decoding has been performed on the provided data.
        '''

class IDevise(metaclass=abc.ABCMeta):
    '''
    The specification for the constructor of decoded objects.
    '''
    __slots__ = ()
    
    @abc.abstractclassmethod
    def get(self, target):
        '''
        Get the value represented by the constructor from the provided target.
        
        @param target: object
            The target to get the value from.
        @return: object
            The constructed object from the target.
        '''
        
    @abc.abstractclassmethod
    def set(self, target, value, support):
        '''
        Set the constructed value into the provided target.
        
        @param target: object
            The target to set the value to.
        @param value: object
            The value object to set to the target.
        @param support: object
            Support context object containing additional data.
        '''
        
# --------------------------------------------------------------------

class Category:
    '''
    Provides the category specification.
    '''
    
    def __init__(self, *info, optional=None):
        '''
        Construct the category of decoders.
        
        @param info: arguments[string]
            The info associated with the category.
        @param optional: boolean|None
            The default optional flag for this category, if None it means that there is no category default.
        '''
        if __debug__:
            for entry in info: assert isinstance(entry, str), 'Invalid info %s' % info
        assert optional is None or isinstance(optional, bool), 'Invalid default optional %s' % optional
        
        self.info = info
        self.optional = optional
        
    def isValid(self, category):
        '''
        Checks if the provided category object is valid for this category.
        
        @param category: object
            The category object to verify.
        @return: boolean
            True if the category is valid for this category.
        '''
        return self == category
    
    def populate(self, categorized):
        '''
        Populate the provided categorized context.
        
        @param categorized: Context
            The categorized context to be populated with data based on this category.
        '''
        assert isinstance(categorized, Categorized), 'Invalid categorized object %s' % categorized
        categorized.category = self
        if categorized.isOptional is None and self.optional is not None: categorized.isOptional = self.optional

class Categorized(Context):
    '''
    Context for categorized definitions. 
    '''
    # ---------------------------------------------------------------- Defined
    category = defines(Category, doc='''
    @rtype: Category
    The definition category.
    ''')
    isOptional = defines(bool, doc='''
    @rtype: boolean
    If True the definition value is optional.
    ''')

CATEGORY_CONTENT = Category('The content properties')
# The constant that defines the content decoding category.

SEPARATOR_CONTENT = '/'
# The separator for content.
