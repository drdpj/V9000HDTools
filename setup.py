from setuptools import setup

setup(
    name='showstat',
    version='0.9.0',
    py_modules=['showstat'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'showstat = showstat:cli',
        ],
    },
)