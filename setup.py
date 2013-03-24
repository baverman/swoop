from setuptools import setup, find_packages

setup(
    name     = 'swoop',
    version  = '0.2dev',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Completely RFC-unaware web scrapper',
    zip_safe   = False,
    packages = find_packages(exclude=['tests']),
    url = 'http://github.com/baverman/swoop',
)
