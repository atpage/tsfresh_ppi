import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tsfresh_ppi",
    version="2021.8.12",
    author="Alex Page",
    author_email="a.t.page@gmail.com",
    description="Add peak-to-peak interval features to tsfresh",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/atpage/tsfresh_ppi",
    project_urls={
        "Bug Tracker": "https://github.com/atpage/tsfresh_ppi/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    # python_requires=">=3.6",
)
