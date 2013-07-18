'''
Created on Jul 15, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from collections import Iterable

# --------------------------------------------------------------------
# The register contexts.
    
class RegisterExcluding(Context):
    '''
    The register context with exclude.
    '''
    # ---------------------------------------------------------------- Required
    exclude = requires(set)
    invokers = requires(list)

# --------------------------------------------------------------------
# The invoker contexts.

class InvokerExcluded(Context):
    '''
    The invoker context to be excluded.
    '''
    # ---------------------------------------------------------------- Required
    id = requires(str)
    location = requires(str)
    
# --------------------------------------------------------------------

def excludeFrom(chain, contexts):
    '''
    Excludes from the chain register the provided invoker and also cancels the chain.
    
    @param chain: Chain
        The chain to exclude and cancel based on.
    @param contexts: Context|Iterable(Context)
        The context(s) with id to be excluded.
    '''
    assert isinstance(chain, Chain), 'Invalid chain %s' % chain
    if not isinstance(contexts, Iterable): contexts = (contexts,)
    assert isinstance(contexts, Iterable), 'Invalid context(s) %s' % contexts
    register = chain.arg.register
    assert RegisterExcluding.exclude in register, 'Invalid register context %s' % chain.arg.register
    assert isinstance(register.exclude, set), 'Invalid exclude set %s' % chain.arg.register.exclude
    
    for ctx in contexts:
        assert InvokerExcluded.id in ctx, 'Invalid invoker %s' % ctx
        assert isinstance(ctx.id, str), 'Invalid invoker id %s' % ctx.id
        register.exclude.add(ctx.id)
    chain.cancel()
