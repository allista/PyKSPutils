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
            "ksp_plugin = KSPUtils.scripts.ksp_plugin:cmd",
            "update_KSP_references = KSPUtils.scripts.update_KSP_references:cmd",
        ],
    },
)
