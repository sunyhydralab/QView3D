from setuptools import setup, find_packages

setup(
    name='qview3dserver',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
    ],
)

