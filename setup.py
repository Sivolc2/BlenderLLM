#!/usr/bin/env python3
"""
Bluesky Monitor Setup
"""

from setuptools import setup, find_packages

setup(
    name="bsky-monitor",
    version="0.1.0",
    description="Monitor Bluesky posts for replies and send notifications to Redpanda",
    author="BlenderLLm Team",
    packages=find_packages(),
    install_requires=[
        "atproto>=0.0.7",
        "kafka-python>=2.0.2",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "bsky-monitor=bsky_monitor.__main__:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 