'''
Created on Oct 2, 2013

@package: ally distribution
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

The entry point module that starts the distribution.
'''

import argparse
import sys
import timeit
import traceback

# --------------------------------------------------------------------

try:
    import package_extender
    package_extender.PACKAGE_EXTENDER.addFreezedPackage('__distribution__.')
    from ally.container import aop, context, support
    from ally.support.util_deploy import Options, PREPARE, DEPLOY
except ImportError:
    print('Corrupted or missing ally component, make sure that this component is not missing from python path '
          'or components eggs', file=sys.stderr)

parser = argparse.ArgumentParser(description='The ally distribution manager.')  # The parser to be prepared.
options = Options()

# --------------------------------------------------------------------

def __distribution__():
    # In the first stage we prepare the application deployment.
    context.open(aop.modulesIn('__distribution__.**'))
    try:
        for call, *_other in support.eventsFor(PREPARE): call()
    
        # In the second stage we parse the application arguments.
        parser.parse_args(namespace=options)
    
        for call, *_other in support.eventsFor(DEPLOY): call()
        
    except SystemExit: raise
    except:
        print('-' * 150, file=sys.stderr)
        print('A problem occurred while deploying', file=sys.stderr)
        traceback.print_exc()
        print('-' * 150, file=sys.stderr)
        sys.exit(1)
    finally: context.deactivate()

if __name__ == '__main__':
    sys.modules['distribution'] = sys.modules['__main__']
    deployTime = timeit.timeit(__distribution__, number=1)
    print('=' * 50, 'Distribution performed in %.2f seconds' % deployTime)
