'''
Created on Feb 18, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing report implementations.
'''

from .spec import IReport, Attributes
from ally.design.processor.spec import IAttribute

# --------------------------------------------------------------------

class ReportUnused(IReport):
    '''
    Implementation for @see: IReport that reports the unused attributes.
    '''
    __slots__ = ('_reports', '_attributes')
    
    def __init__(self):
        '''
        Construct the report.
        '''
        self._reports = {}
        self._attributes = []
        
    def open(self, name):
        '''
        @see: IReport.open
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        report = self._reports.get(name)
        if not report: report = self._reports[name] = ReportUnused()
        return report
        
    def add(self, attributes):
        '''
        @see: IReport.add
        '''
        assert isinstance(attributes, Attributes), 'Invalid attributes %s' % attributes
        self._attributes.append(attributes)
        
    def report(self):
        '''
        Creates the report lines.
        
        @return: list[string]
            The list of string lines.
        '''
        st, reported = [], set()
        for attributes in self._attributes:
            assert isinstance(attributes, Attributes)
            for key, attribute in attributes.iterate():
                assert isinstance(attribute, IAttribute)
                if not attribute.isUsed():
                    if key not in reported:
                        reported.add(key)
                        st.append(('%s.%s for %s' % (key + (attribute,))).strip())
        if st: st.insert(0, 'Unused attributes:')
            
        for name, report in self._reports.items():
            assert isinstance(report, ReportUnused)
            lines = report.report()
            if lines:
                st.append('Report on %s:' % name)
                st.extend('\t%s' % line for line in lines)
        return st
