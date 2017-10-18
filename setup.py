# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

setup(
    name='rb_call',
    version='0.0.1',
    description='A library to call Ruby methods from a Python script. You can combine a Python script and Ruby libraries.',
    long_description=readme,
    author='yohm',
    author_email='yohm@users.noreply.github.com',
    url='https://github.com/cryptomelone/rb_call',
    license=None,
    packages=find_packages(exclude=('tests', 'patch')),
    package_data={"rb_call": ["rb_call_server.rb"]},
    install_requires=["msgpack-python", "msgpack-rpc-python"]
)