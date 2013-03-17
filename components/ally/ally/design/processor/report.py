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
    __slots__ = ('reports', 'resolvers')
    
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
        #TODO: Gabriel: make a prettier report.
        lines = []
        reportOn(lines, self.resolvers, LIST_UNUSED)
        if lines: lines.insert(0, 'Unused attributes:')
            
        for name, report in self.reports.items():
            assert isinstance(report, ReportUnused)
            linesChild = report.report()
            if linesChild:
                lines.append('Report on %s' % name)
                lines.extend('%s%s' % (self.ident, line) for line in linesChild)
        return lines
