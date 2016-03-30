from setuptools import setup

setup(name='miracl_api',
      version='0.1',
      description='SDK for using Miracl authentication',
      url='https://github.com/miracl/maas-sdk-python',
      author='Elviss Kustans',
      author_email='n3o59hf@gmail.com',
      license='TBD',
      packages=['miracl_api'],
      install_requires=[
          'flask', 'oic',
      ],
      zip_safe=False)
