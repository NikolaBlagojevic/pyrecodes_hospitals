from setuptools import setup, find_packages

setup(
    name='pyrecodes_hospitals',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.24.2',
        'pandas>=2.0.0',
        'geopandas>=0.12.2',
        'matplotlib>=3.7.1',
    ],
)