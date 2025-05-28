# setup.py
from setuptools import setup

setup(
    name="ArticleSearch",
    version="2.0",
    description="Zoekapplicatie voor artikeldetails, stockinfo en afbeeldingen",
    author="TheRealBarremans",
    packages=["."],
    install_requires=[
        "PySide6>=6.6.0",
        "requests>=2.31.0",
        "urllib3>=1.26.0",
        "certifi>=2023.7.22",
        "chardet>=5.1.0",
        "idna>=3.4",
        "Pillow>=10.2.0"
    ],
    python_requires='>=3.8',
)
