"""Setup script for Purisa backend package."""
from setuptools import setup, find_packages

setup(
    name="purisa",
    version="0.1.0",
    description="Multi-platform social media bot detection system",
    author="Purisa Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.25",
        "alembic>=1.13.1",
        "httpx>=0.26.0",
        "atproto>=0.0.40",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "apscheduler>=3.10.4",
        "python-multipart>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "purisa=purisa.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
