from setuptools import setup, find_packages


setup(
    name='uavsim',
    version='0.0.2',
    packages=find_packages(),
    # setup_requires=['pytest-runner'],
    # tests_require=['pytest'],
    package_dir={'': 'src'},
    package_data={'': ['*']},
    url='https://github.com/kamikaze/uavsim',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    keywords='uav simulator',
    install_requires=(
        'pyserial',
        'autobahn',
        'crossbar',
        'PyQt5',
        'idna<2.6',

        'numpy',
        'h5py',
        'pyqtgraph',
    ),
    author='Oleg Korsak',
    author_email='kamikaze.is.waiting.you@gmail.com',
    description='UAV Simulator',
    test_suite='tests'
)
