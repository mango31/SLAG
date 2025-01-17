from setuptools import setup, find_packages

setup(
    name="vMini-engine",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "pydantic==2.4.2",
        "pydantic-settings==2.1.0",
        "boto3==1.29.3",
        "python-dotenv==1.0.0",
        "redis==5.0.1",
        "pinecone-client==2.2.4",
        "aiohttp==3.9.1",
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1"
    ],
) 