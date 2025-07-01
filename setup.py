from setuptools import setup

setup(
    name="OctoRAG",
    version="0.1",
    py_modules=["main", "octorag", "octorag_tools"],
    entry_points={
        "console_scripts": [
            "octorag = main:main",
        ],
    },
)
