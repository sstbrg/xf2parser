from setuptools import setup, find_packages

with open('requirements.txt') as fp:
    install_requires = fp.read()

    setup(
        name='xtrbtparser',
        version='1.84',
        author='Stas Steinberg (X-trodes LTD)',
        author_email='stas@xtrodes.com',
        packages=['xtrbtparser'],
        include_package_data=True,
        license='GNU GPLv3',
        long_description=open('README.md').read(),
        url="https://bitbucket.org/xtrodesalgorithms/xtr-bt",
        install_requires=install_requires
    )