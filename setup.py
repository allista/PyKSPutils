from setuptools import setup, find_packages

setup(
    name="PyKSPutils",
    version="1.3.0",
    author="Allis Tauri",
    author_email="allista@gmail.com",
    description="A collection of tools and utility classes for KSP modders.",
    license="MIT",
    url="",
    packages=find_packages(),
    python_requires=">=3.8",
    scripts=[
        "grep_parts",
        "select_from_parts",
    ],
    entry_points={
        "console_scripts": [
            "check_project = KSPUtils.scripts.check_project:cmd",
            "git_tag_by_assembly_info = KSPUtils.scripts.git_tag_by_assembly_info:cmd",
            "publish_release = KSPUtils.scripts.publish_release:cmd",
            "update_KSP_references = KSPUtils.scripts.update_KSP_references:cmd",
            "make_mod_release = KSPUtils.scripts.make_mod_release:cmd",
        ],
    },
)
