'''
Created on June 14, 2012

@package: acl gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name="support_acl_gateway",
    version="1.0",
    packages=find_packages(),
    install_requires=['support_acl >= 1.0', 'gateway_http >= 1.0'],
    platforms=['all'],
    zip_safe=True,

    # metadata for upload to PyPI
    author="Gabriel Nistor",
    author_email="gabriel.nistor@sourcefabric.org",
    description="Security for HTTP gateway",
    long_description='Support for access control layer for HTTP gateway',
    license="GPL v3",
    keywords="Ally REST framework acl gateway plugin",
    url="http://www.sourcefabric.org/en/superdesk/",  # project home page
)
