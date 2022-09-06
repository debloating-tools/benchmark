from setuptools import setup

setup(
    name='prodebench',
    version='0.1',
    py_modules=['prodebench'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        pdbench=prodebench:core.cli
    ''',
)
