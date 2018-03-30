from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

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
    install_requires=reqs,
    author='Oleg Korsak',
    author_email='kamikaze.is.waiting.you@gmail.com',
    description='UAV Simulator',
    test_suite='tests'
)
