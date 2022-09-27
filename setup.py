from setuptools import setup

setup(
    name='gridfinity',
    version='0.1',
    install_requires=[
        'cadquery2>=2.1.1',
    ],
    python_requires='>=3.8.0',
    scripts=[
        'scripts/gridfinity-box.py',
    ],
)
