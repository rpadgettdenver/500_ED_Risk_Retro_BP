from setuptools import setup, find_packages

setup(
    name="energize_denver_eaas",
    version="0.1.0",
    author="Your Name",
    author_email="rpadgett@clms.com",
    description="Energize Denver Risk & Retrofit Strategy Platform",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "google-cloud-storage>=2.10.0",
        "google-cloud-bigquery>=3.11.0",
        "pandas>=2.0.0",
        "numpy>=1.26.0",
        "pyarrow>=14.0.0",
    ],
)
