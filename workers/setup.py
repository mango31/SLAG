from setuptools import setup, find_packages

setup(
    name="vmini-engine-worker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.4.2",
        "pydantic-settings>=2.1.0",
        "boto3>=1.29.3",
        "python-dotenv>=1.0.0",
        "redis[hiredis]>=5.0.1",
        "pinecone-client>=2.2.4"
    ]
) 