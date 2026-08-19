from setuptools import find_packages, setup

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip()]

with open("dashboard/__init__.py") as f:
    version = f.read().split('__version__ = "')[1].split('"')[0]

setup(
    name="dashboard",
    version=version,
    description="Configurable ERPNext overview dashboard",
    author="Surajwit",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
