# -*- coding: utf-8 -*-

"""
@Author  :   Xu

@Software:   PyCharm

@File    :   setup.py

@Time    :   2020/9/17 7:20 下午

@Desc    :   version information

"""
from setuptools import setup

packages = \
['wechatter',
 ]

package_data = \
{'': ['*'],
 'wechatter.dm': ['schemas/*']}

install_requires = [
 'tensorflow>=2.1']

extras_require = {}

entry_points = \
{'console_scripts': ['wechatter = wechatter.__main__:main']}

setup_kwargs = {
    'name': 'wechatter',
    'version': '1.0.0',
    'description': 'Open source deep learning framework to automate text- and voice-based conversations',
    'long_description': '# wechatter Open Source',
    'author': 'wechatter community',
    'author_email': 'charlesxu86@163.com',
    'maintainer': 'wechatter',
    'maintainer_email': 'charlesxu86@163.com',
    'url': 'https://we-chatter.com',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.6',
}


setup(**setup_kwargs)
