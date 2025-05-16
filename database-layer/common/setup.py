from setuptools import setup, find_packages

setup(
    name="database-layer-common",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.23.0",
    ],
    author="PrismicX Team",
    author_email="team@prismicx.io",
    description="Common libraries for the database layer",
    keywords="database, microservice, task, repository",
    python_requires=">=3.8",
) 