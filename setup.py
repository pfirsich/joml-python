import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="joml",
    version="0.0.1",
    author="Joel Schumacher",
    author_email="joelschum@gmail.com",
    description="A parser library for [JOML](https://github.com/pfirsich/joml",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pfirsich/joml-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=["lark-parser>=0.11.3"],
    entry_points={"console_scripts": ["joml2json=joml.joml2json:main"],},
)
