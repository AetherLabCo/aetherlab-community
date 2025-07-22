"""Setup configuration for AetherLab Python SDK."""

from setuptools import setup, find_packages
import os

# Read the README for long description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="aetherlab",
    version="0.2.1",
    author="AetherLab",
    author_email="support@aetherlab.ai",
    description="Official Python SDK for AetherLab's AI Guardrails and Compliance Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AetherLabCo/aetherlab-community",
    project_urls={
        "Bug Tracker": "https://github.com/AetherLabCo/aetherlab-community/issues",
        "Documentation": "https://docs.aetherlab.ai",
        "Source Code": "https://github.com/AetherLabCo/aetherlab-community",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "twine>=4.0.0",
            "wheel>=0.38.0",
        ],
    },
    keywords="aetherlab ai guardrails compliance safety llm security content-moderation prompt-injection ai-safety chatbot-safety ml-security artificial-intelligence machine-learning nlp openai anthropic gpt claude gemini mistral llama ai-governance responsible-ai",
) 