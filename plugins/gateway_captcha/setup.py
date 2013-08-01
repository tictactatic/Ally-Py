'''
Created on June 14, 2012

@package: captcha
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name="captcha",
    version="1.0",
    packages=find_packages(),
    install_requires=['support_acl >= 1.0', 'gateway >= 1.0'],
    platforms=['all'],
    zip_safe=True,

    # metadata for upload to PyPI
    author="Gabriel Nistor",
    author_email="gabriel.nistor@sourcefabric.org",
    description="Provides captcha gateways for validation",
    long_description='Provides captcha gateways for validation',
    license="GPL v3",
    keywords="Ally REST framework captcha gateway validation plugin",
    url="http://www.sourcefabric.org/en/superdesk/",  # project home page
)
