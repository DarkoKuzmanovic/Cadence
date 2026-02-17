"""
Setup script for Cadence installer.

For modern installation, use pyproject.toml with:
    pip install .

For development:
    pip install -e .[dev]
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
repository_root = Path(__file__).parent
long_description = (repository_root / "README.md").read_text(encoding="utf-8")

setup(
    name="cadence-installer",
    version="1.0.0",
    author="Darko Kuzmanovic",
    author_email="darko.kuzmanovic@gmail.com",
    description="Automated installer for the Cadence multi-agent orchestration system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DarkoKuzmanovic/Cadence",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "textual>=0.47.0",
        "rich>=13.0.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cadence-install=install:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    keywords="vscode copilot agents installer tui cli",
    project_urls={
        "Homepage": "https://github.com/DarkoKuzmanovic/Cadence",
        "Issues": "https://github.com/DarkoKuzmanovic/Cadence/issues",
        "Changelog": "https://github.com/DarkoKuzmanovic/Cadence/blob/main/CHANGELOG.md",
    },
)
