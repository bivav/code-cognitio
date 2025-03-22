from setuptools import setup, find_packages

setup(
    name="code-cognitio",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "nltk>=3.7.0",
        "spacy>=3.5.0",
        "faiss-cpu>=1.7.4",
        "sentence-transformers>=2.2.2",
        "python-magic>=0.4.27",
        "beautifulsoup4>=4.11.0",
        "markdown>=3.4.0",
        "docutils>=0.19.0",
        "tqdm>=4.64.0",
        "numpy>=1.23.0",
        "regex>=2022.10.31",
    ],
)
