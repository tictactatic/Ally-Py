'''
Created on June 14, 2012

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name='service_assemblage',
    version='1.0',
    packages=find_packages(),
    install_requires=['ally_http >= 1.0'],
    platforms=['all'],
    test_suite='test',
    zip_safe=True,
    package_data={
        '': ['*.zip'],
    },

    # metadata for upload to PyPI
    author='Gabriel Nistor',
    author_email='gabriel.nistor@sourcefabric.org',
    description='Ally framework - assemblage service',
    long_description='The assemblage service of the Ally framework',
    license='GPL v3',
    keywords='Ally HTTP framework assemblage',
    url='http://www.sourcefabric.org/en/superdesk/',  # project home page
)
