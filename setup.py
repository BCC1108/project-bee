from setuptools import setup, find_packages

setup(
    name='project-bee',
    version='0.1.0',
    description='Cryptocurrency Trading & Backtesting Framework',
    author='baronfkingCEE',
    url='https://gitee.com/baronfkingCEE/project-bee',
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[line.strip() for line in open('requirements.txt').readlines() if line.strip()],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
