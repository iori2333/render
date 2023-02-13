from setuptools import setup, find_packages
import os.path as osp

cwd = osp.dirname(osp.abspath(__file__))
cvext_path = osp.join(cwd, "cvext")

setup(
    name="render",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.2",
        "Pillow>=9.4.0",
        "opencv-python>=4.5.4.58",
        "pymixbox==2.0.0",
        "Pyphen>=0.13.2",
        "typing_extensions>=3.10.0.2",
        f"cv_extensions @ file://{cvext_path}",
    ],
)
