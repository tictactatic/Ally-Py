'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Finds the invoker matching the allow pattern.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.internationalization import _

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    root = requires(Context)
    
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    child = requires(Context)
    childByName = requires(dict)

class Allow(Context):
    '''
    The allow context.
    '''
    # ---------------------------------------------------------------- Defined
    invoker = defines(Context, doc='''
    @rtype: Context
    The located invoker for the allow request.
    ''')
    suggestion = defines(tuple, doc='''
    @rtype: tuple(string, dictionary{string: object})
    The pattern suggestion, having on the first position the suggestion message and on the second position the 
    data dictionary for message place holders.
    ''')
    methodsAllowed = defines(set, doc='''
    @rtype: set(string)
    The allowed methods for the identified pattern, this is available only if the pattern is valid but the method
    is not known.
    ''')
    # ---------------------------------------------------------------- Required
    pattern = requires(str)
    method = requires(str)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='findAllowInvoker')
class FindAllowInvoker(HandlerProcessor):
    '''
    Implementation for a processor that finds the invoker matching the allow pattern.
    '''
    
    input_place_holders = ['*', '#']; wire.config('input_place_holders', doc='''
    The allow access pattern place holders that are placed where a identifier is expected. 
    ''')
    
    def __init__(self):
        assert isinstance(self.input_place_holders, str), 'Invalid input place holders %s' % self.input_place_holders
        super().__init__(Node=Node)
        
        self._placeHolders = set(self.input_place_holders)

    def process(self, chain, register:Register, allow:Allow=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the solved inputs.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not allow: return  # No allow to process.
        assert isinstance(allow, Allow), 'Invalid allow %s' % allow
        assert isinstance(allow.pattern, str), 'Invalid allow pattern %s' % allow.pattern
        
        paths = allow.pattern.uri.split('/')
        node = register.root
        for k, path in enumerate(paths):
            assert isinstance(node, Node), 'Invalid node %s' % node
            
            if path in self._placeHolders:
                if node.child: node = node.child
                else:
                    if node.childByName:
                        allow.suggestion = (_('Instead of first place holder in \'%(path)s\' or before it is '
                                              'expected one of: %(names)s'),
                                            dict(path='/'.join(paths[:k]), names=sorted(node.childByName)))
                    else:
                        allow.suggestion = _('No more path items expected after \'%(path)s\''), dict(path='/'.join(paths[:k]))
                    return chain.cancel()
                
            elif node.childByName:
                if path not in node.childByName:
                    allow.suggestion = (_('Instead of \'%(item)s\' or before it is expected: %(names)s'),
                                        dict(item=path, names=sorted(node.childByName)))
                    return chain.cancel()
                node = node.childByName[path]
                
            elif node.child:
                allow.suggestion = (_('Instead of \'%(item)s\' or before it is expected one of place holders: %(holders)s'),
                                    dict(item=path, holders=self.input_place_holders))
                return chain.cancel()
            else:
                allow.suggestion = (_('No more path items expected after \'%(path)s\''), dict(path='/'.join(paths[:k])))
                return chain.cancel()
                
        if not node.invokers:
            if node.childByName:
                allow.suggestion = (_('Expected additional path items, one of: %(names)s'),
                                    dict(names=sorted(node.childByName)))
            else: allow.suggestion = (_('Expected one of place holders: %(holders)s'), dict(holders=self.input_place_holders))
            return chain.cancel()
        
        if allow.method not in node.invokers:
            allow.methodsAllowed = set(node.invokers)
            return chain.cancel()
        
        allow.invoker = node.invokers[allow.method]
            
