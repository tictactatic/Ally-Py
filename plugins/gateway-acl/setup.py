'''
Created on June 14, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name="gateway_acl",
    version="1.0",
    packages=find_packages(),
    install_requires=['gateway >= 1.0'],
    platforms=['all'],
    zip_safe=True,

    # metadata for upload to PyPI
    author="Gabriel Nistor",
    author_email="gabriel.nistor@sourcefabric.org",
    description="Ally framework - gateway acl",
    long_description='The plugin that provides the gateway based on services access control layer',
    license="GPL v3",
    keywords="Ally REST framework plugin gateway services access control layer",
    url="http://www.sourcefabric.org/en/superdesk/",  # project home page
)
