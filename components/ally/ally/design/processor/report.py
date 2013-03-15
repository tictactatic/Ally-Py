'''
Created on Feb 18, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing report implementations.
'''

from .spec import IReport, IRepository, LIST_UNUSED, LIST_CLASSES
from ally.support.util_sys import locationStack
from collections import Iterable

# --------------------------------------------------------------------

class ReportUnused(IReport):
    '''
    Implementation for @see: IReport that reports the unused attributes resolvers.
    '''
    __slots__ = ('reports', 'repositories')
    
    ident = '  '
    # The ident to use in the report.
    
    def __init__(self):
        '''
        Construct the report.
        '''
        self.reports = {}
        self.repositories = []
        
    def open(self, name):
        '''
        @see: IReport.open
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        report = self.reports.get(name)
        if not report: report = self.reports[name] = ReportUnused()
        return report
        
    def add(self, repository):
        '''
        @see: IReport.add
        '''
        assert isinstance(repository, IRepository), 'Invalid resolvers %s' % repository
        self.repositories.append(repository)
        
    def report(self):
        '''
        Creates the report lines.
        
        @return: list[string]
            The list of string lines.
        '''
        st, reported = [], set()
        for repository in self.repositories:
            assert isinstance(repository, IRepository)
            for key, classes in repository.listAttributes(LIST_UNUSED, LIST_CLASSES).items():
                if key not in reported:
                    reported.add(key)
                    st.append('%s%s' % (self.ident, '%s.%s used in:' % key))
                    assert isinstance(classes, Iterable), 'Invalid classes %s' % classes
                    for clazz in classes: st.append('%s%s' % (self.ident, locationStack(clazz).strip()))
                        
        if st: st.insert(0, 'Unused attributes:')
            
        for name, report in self.reports.items():
            assert isinstance(report, ReportUnused)
            lines = report.report()
            if lines:
                st.append('Report on %s:' % name)
                st.extend('%s%s' % (self.ident, line) for line in lines)
        return st
