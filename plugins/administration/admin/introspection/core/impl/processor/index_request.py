'''
Created on Sep 24, 2013

@package: introspection
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that indexes the @see: Request objects on the assembler register.
'''

from ally.api.operator.type import TypeProperty, TypeCall, TypeService
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from binascii import crc32
from collections import OrderedDict
from pydoc import getdoc
import re
from ally.support.util_spec import IDo

# --------------------------------------------------------------------
#TODO: Gabriel: continue
class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    intrRequests = defines(OrderedDict, doc='''
    @rtype: dictionary{integer: Request}
    The dictionary containing the request model instances indexed by the id.
    ''')
    intrInvokers = defines(dict, doc='''
    @rtype: dictionary{integer: Context}
    The dictionary containing the invoker context instances indexed by the id.
    ''')
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    intrInputs = defines(OrderedDict, doc='''
    @rtype: dictionary{string: Input}
    The introspection inputs indexed by the input name. 
    ''')
    # ---------------------------------------------------------------- Required
    id = requires(str)
    call = requires(TypeCall)
    methodHTTP = requires(str)
    path = requires(list)
    shadowing = requires(Context)
    doInvoke = requires(IDo)
    
class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)
      
# --------------------------------------------------------------------

@setup(Handler, name='indexRequest')
class IndexRequestHandler(HandlerProcessor):
    '''
    Provides the indexes of the @see: Request objects on the assembler register.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Element=Element)
    
    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Index the introspection request object.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        if register.intrInvokers: return  # The requests are already populated.
        
        register.intrInvokers, requests = {}, []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            assert isinstance(invoker.id, str), 'Invalid invoker id %s' % invoker.id
            
            items, invoker.intrInputs = [], OrderedDict()
            for el in invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if el.property is None:
                    assert isinstance(el.name, str), 'Invalid name %s' % el.name
                    items.append(el.name)
                    continue
                assert isinstance(el.property, TypeProperty), 'Invalid property %s' % el.property
                name = str(len(invoker.intrInputs) + 1)
                items.append('{%s}' % name)
                
                inp = invoker.intrInputs[name] = Input()
                inp.Name = name
                inp.Type = str(el.property)
                inp.Mandatory = True
                inp.Description = _('The %(type)s of %(model)s %(description)s') % \
                        dict(type=_(el.property.name), model=_(el.property.parent.name),
                        description=re.sub('[\s]+', ' ', getdoc(el.property.parent.clazz) or '...'))
            
            req = Request()
            requests.append(req)
            
            req.Id = self.asId(invoker)
            req.Path = '/'.join(items)
            req.Method = invoker.methodHTTP
            
            if invoker.call:
                assert isinstance(invoker.call, TypeCall), 'Invalid call %s' % invoker.call
                assert isinstance(invoker.call.parent, TypeService), 'Invalid service %s' % invoker.call.parent
                
                sclazz = invoker.call.parent.clazz
                req.Name = invoker.call.name
                req.APIClass = '%s.%s' % (sclazz.__module__, sclazz.__name__)
                req.APIDoc = getdoc(getattr(invoker.call.definer, invoker.call.name))
                
                
            
#        info = invoker.infoIMPL
#        assert isinstance(info, InvokerInfo)
#
#        m.IMPLDoc = info.doc
#        if info.clazz: m.IMPL = info.clazz.__module__ + '.' + info.clazz.__name__
#        else: m.IMPL = '<unknown>'
#
#        if info.clazzDefiner:
#            m.IMPLDefiner = info.clazzDefiner.__module__ + '.' + info.clazzDefiner.__name__
#        else: m.IMPLDefiner = m.IMPL
#
#        if invoker.infoAPI:
#            info = invoker.infoAPI
#            assert isinstance(info, InvokerInfo)
#
#            m.APIDoc = info.doc
#            if info.clazz: m.APIClass = info.clazz.__module__ + '.' + info.clazz.__name__
#            else: m.APIClass = '<unknown>'
#
#            if info.clazzDefiner:
#                m.APIClassDefiner = info.clazzDefiner.__module__ + '.' + info.clazzDefiner.__name__
#            else: m.APIClassDefiner = m.APIClass
            
            if invoker.shadowing:
                assert isinstance(invoker.shadowing, Invoker), 'Invalid invoker %s' % invoker.shadowing 
                req.ShadowOf = self.asId(invoker.shadowing)
            
            register.intrInvokers[req.Id] = invoker
        
        requests.sort(key=lambda req: req.Method)
        requests.sort(key=lambda req: req.Path)
        register.intrRequests = OrderedDict((req.Id, req) for req in requests)

    # ----------------------------------------------------------------

    def asId(self, invoker):
        '''
        Provides the id of the invoker.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        return crc32(invoker.id.encode(), crc32(invoker.methodHTTP.encode()))


# def _refresh(self):
#        '''
#        Refreshes the requests.
#        '''
#        if self._reset:
#            self._requestId = 1
#            self._inputId = 1
#            self._methodId = 1
#    
#            self._nodeRequests = {}
#            self._requests = OrderedDict()
#            self._patternInputs = {}
#            self._inputs = OrderedDict()
#            self._requestMethods = {}
#            self._methods = OrderedDict()
#
#            replacer = ReplacerMarkCount()
#            for path in iteratePaths(self.resourcesRoot): self._process(path, replacer)
#            self._reset = False
#
#    def _process(self, path, replacer):
#        '''
#        Processes the node and sub nodes requests.
#        '''
#        assert isinstance(path, Path), 'Invalid path %s' % path
#        assert isinstance(replacer, ReplacerMarkCount), 'Invalid replacer %s' % replacer
#        node = path.node
#        assert isinstance(node, Node), 'Invalid path node %s' % node
#        if node in self._nodeRequests: return
#        if not (node.get or node.delete or node.insert or node.update): return
#        
#        r = Request()
#        r.Id = self._requestId
#        
#        replacer.reset()
#        r.Pattern = '/'.join(path.toPaths(self.converterPath, replacer))
#
#        patternInputs = set()
#        for name, match in replacer.replaced.items():
#            inp = self._toPatternInput(match, r)
#            patternInputs.add(inp.Id)
#            inp.Name = name
#
#        self._requests[r.Id] = r
#        self._nodeRequests[node] = r.Id
#        self._patternInputs[r.Id] = patternInputs
#        requestMethods = self._requestMethods[r.Id] = set()
#
#        self._requestId += 1
#
#        if node.get:
#            m = self._toMethod(node.get, r); requestMethods.add(m.Id)
#            r.Get = m.Id
#        if node.delete:
#            m = self._toMethod(node.delete, r); requestMethods.add(m.Id)
#            r.Delete = m.Id
#        if node.insert:
#            m = self._toMethod(node.insert, r); requestMethods.add(m.Id)
#            r.Insert = m.Id
#        if node.update:
#            m = self._toMethod(node.update, r); requestMethods.add(m.Id)
#            r.Update = m.Id
#
#    def _toPatternInput(self, match, req):
#        '''
#        Processes the match as a pattern input.
#        '''
#        assert isinstance(req, Request)
#        inp = Input()
#        inp.Id = self._inputId
#        self._inputs[self._inputId] = inp
#
#        self._inputId += 1
#
#        inp.Mandatory = True
#        inp.ForRequest = req.Id
#
#        if isinstance(match, MatchProperty):
#            assert isinstance(match, MatchProperty)
#            assert isinstance(match.node, NodeProperty)
#            typ = next(iter(match.node.typesProperties))
#            assert isinstance(typ, TypeModelProperty)
#            inp.Description = _('The %(type)s of %(model)s %(description)s') % \
#                        dict(type=_(typ.property), model=_(typ.container.name),
#                        description=re.sub('[\s]+', ' ', getdoc(typ.parent.clazz) or '...'))
#        else:
#            raise DevelError('Unknown match %s' % match)
#
#        return inp
#
#    def _toMethod(self, invoker, req):
#        '''
#        Processes the method based on the invoker.
#        '''
#        assert isinstance(invoker, Invoker)
#        assert isinstance(req, Request)
#        m = Method()
#        m.Id = self._methodId
#        self._methods[self._methodId] = m
#
#        m.ForRequest = req.Id
#
#        self._methodId += 1
#
#        m.Name = invoker.name
#        m.Type = self.methodNames.get(invoker.method, '<unknown>')
#
#        info = invoker.infoIMPL
#        assert isinstance(info, InvokerInfo)
#
#        m.IMPLDoc = info.doc
#        if info.clazz: m.IMPL = info.clazz.__module__ + '.' + info.clazz.__name__
#        else: m.IMPL = '<unknown>'
#
#        if info.clazzDefiner:
#            m.IMPLDefiner = info.clazzDefiner.__module__ + '.' + info.clazzDefiner.__name__
#        else: m.IMPLDefiner = m.IMPL
#
#        if invoker.infoAPI:
#            info = invoker.infoAPI
#            assert isinstance(info, InvokerInfo)
#
#            m.APIDoc = info.doc
#            if info.clazz: m.APIClass = info.clazz.__module__ + '.' + info.clazz.__name__
#            else: m.APIClass = '<unknown>'
#
#            if info.clazzDefiner:
#                m.APIClassDefiner = info.clazzDefiner.__module__ + '.' + info.clazzDefiner.__name__
#            else: m.APIClassDefiner = m.APIClass
#
#        return m
#
## --------------------------------------------------------------------
