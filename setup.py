from setuptools import setup, find_packages

setup(
    name='task_executor',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'fire>=0.5.0',
        'greenlet>=3.0.1',
        'six>=1.16.0',
        'SQLAlchemy>=2.0.22',
        'termcolor>=2.3.0',
        'tqdm>=4.66.1',
        'typing_extensions>=4.8.0'
    ],
)
