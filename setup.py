from distutils.core import setup

setup(
        name='PyKSPutils',
        version='1.0',
        packages=['KSPUtils'],
        scripts=['make_mod_release', 'grep_parts', 'select_from_parts', 'update_KSP_references'],
        url='',
        license='MIT',
        author='Allis Tauri',
        author_email='allista@gmail.com',
        description='A collection of tools and utility classes for KSP modders.'
)
