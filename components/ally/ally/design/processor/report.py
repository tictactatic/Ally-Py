'''
Created on Feb 18, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing report implementations.
'''

from .resolvers import reportOn
from .spec import IReport, LIST_UNUSED

# --------------------------------------------------------------------

class ReportUnused(IReport):
    '''
    Implementation for @see: IReport that reports the unused attributes resolvers.
    '''
    
    ident = '  '
    # The ident to use in the report.
    
    def __init__(self):
        '''
        Construct the report.
        '''
        self.reports = {}
        self.resolvers = {}
        
    def open(self, name):
        '''
        @see: IReport.open
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        report = self.reports.get(name)
        if not report: report = self.reports[name] = ReportUnused()
        return report
        
    def add(self, resolvers):
        '''
        @see: IReport.add
        '''
        assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
        self.resolvers.update(resolvers)
        
    def report(self):
        '''
        Creates the report lines.
        
        @return: list[string]
            The list of string lines.
        '''
        data = self.process(set())
        if data:
            message, stack = data
            assert isinstance(stack, list), 'Invalid stack %s' % stack
            if len(stack) > 1:
                return 'Unused attributes in %s\n%s\n, found in\n%s' % (stack[0], message, '\n'.join(stack[1:]))
            elif stack:
                return 'Unused attributes in %s\n%s' % (stack[0], message)
            return message

    # ----------------------------------------------------------------
    
    def process(self, reported):
        '''
        Process the report.
        '''
        assert isinstance(reported, set), 'Invalid reported names %s' % reported
        
        datas = []
        for name, report in self.reports.items():
            assert isinstance(report, ReportUnused)
            if name in reported: continue
            data = report.process(reported)
            if data:
                reported.add(name)
                _message, stack = data
                assert isinstance(stack, list), 'Invalid stack %s' % stack
                stack.append(name)
                datas.append(data)
        
        messages = reportOn([], self.resolvers, LIST_UNUSED)

        if messages or len(datas) > 1:
            for message, stack in datas:
                if len(stack) > 1:
                    messages.append('Unused attributes in %s\n%s\n, found in\n%s' % (stack[0], message, '\n'.join(stack[1:])))
                else:
                    messages.append('Unused attributes in %s\n%s' % (stack[0], message))
                    
            return '\n'.join(messages), []
        elif datas:
            return datas[0]
        
