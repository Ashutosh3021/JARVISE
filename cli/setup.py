"""
JARVIS CLI Setup

Install CLI:
    pip install -e .
    
Usage:
    jarvis --help
    jarvis chat "Hello"
    jarvis shell
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="jarvis-cli",
    version="1.0.0",
    author="JARVIS Team",
    description="Command-line interface for JARVIS AI Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "aiohttp>=3.9.0",
        "websockets>=12.0",
        "requests>=2.31.0",
        "prompt-toolkit>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jarvis=cli.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
