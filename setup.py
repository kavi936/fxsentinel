#!/usr/bin/env python3
"""
Setup script for FXSentinel
"""

from setuptools import setup, find_packages

setup(
    name="fxsentinel",
    version="1.0.0",
    description="AI-Powered Forex Trading Dashboard",
    author="FXSentinel Team",
    packages=find_packages(),
    install_requires=[
        "Flask>=2.3.0",
        "Flask-CORS>=4.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "gunicorn>=21.0.0",
        "openai>=1.0.0",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "fxsentinel=wsgi:main",
        ],
    },
) 