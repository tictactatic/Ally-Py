'''
Created on Jul 10, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the categorization of decoders.
'''

from ally.container.ioc import injected
from ally.core.impl.encdec import DecoderDelegate
from ally.core.spec.transform.encdec import Categorized, Category
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    categoriesDecoded = defines(set, doc='''
    @rtype: set(Category)
    A set of the categories that have decoding available for the invoker.
    ''')
    
class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    decoders = defines(list)
    definitions = defines(list)
    # ---------------------------------------------------------------- Required
    solicitations = requires(list)

class Support(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Required
    category = requires(object)

class CreateCategorize(Context):
    '''
    The create categorise decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    category = defines(Category, doc='''
    @rtype: Category
    The create category.
    ''')
    solicitations = defines(list)
    # ---------------------------------------------------------------- Required
    decoders = requires(list)
    definitions = requires(list)
    
# --------------------------------------------------------------------

@injected
class CategorizeHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the categorization of decoders.
    '''
    
    categoryAssembly = Assembly
    # The category decode processors to be used for decoding.
    category = Category
    # The category to be used.
    
    def __init__(self):
        assert isinstance(self.categoryAssembly, Assembly), 'Invalid category assembly %s' % self.categoryAssembly
        assert isinstance(self.category, Category), 'Invalid category %s' % self.category
        super().__init__(Branch(self.categoryAssembly).using(create=CreateCategorize).included(),
                         Definition=Categorized, Support=Support)

    def process(self, chain, processing, invoker:Invoker, create:Create, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the categories the decoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        keyargs.update(invoker=invoker)
        arg = processing.executeWithAll(create=processing.ctx.create(category=self.category,
                                                                     solicitations=create.solicitations), **keyargs)
        assert isinstance(arg.create, CreateCategorize), 'Invalid create %s' % arg.create
        
        if arg.create.decoders:
            if invoker.categoriesDecoded is None: invoker.categoriesDecoded = set()
            invoker.categoriesDecoded.add(self.category) 
            if create.decoders is None: create.decoders = []
            create.decoders.append(DecoderCategorise(arg.create.decoders, self.category))
        if arg.create.definitions:
            for defin in arg.create.definitions: self.category.populate(defin)
                    
            if create.definitions is None: create.definitions = arg.create.definitions
            else: create.definitions.extend(arg.create.definitions)
        
# --------------------------------------------------------------------

class DecoderCategorise(DecoderDelegate):
    '''
    Extension of the delegate decoder that only applies for a certain support category.
    '''
    
    def __init__(self, decoders, category):
        '''
        @see: DecoderDelegate.__init__
        
        @param category: Category
            The category to delegate for.
        '''
        assert isinstance(category, Category), 'Invalid category %s' % category
        super().__init__(decoders)
        
        self.category = category
        
    def decode(self, path, obj, target, support):
        '''
        @see: DecoderDelegate.decode
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        if not self.category.isValid(support.category): return False
        
        return super().decode(path, obj, target, support)
