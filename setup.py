from setuptools import setup, find_packages

setup(
        name='PyKSPutils',
        version='1.0',
        scripts=['make_mod_release', 'grep_parts', 'select_from_parts', 'update_KSP_references'],
        url='',
        license='MIT',
        author='Allis Tauri',
        author_email='allista@gmail.com',
        description='A collection of tools and utility classes for KSP modders.'
    packages=find_packages(),
)
