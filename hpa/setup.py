from setuptools import setup, find_packages

setup(
    name='hpa',
    version='1.0',

    description='HPA discovery package for stevedore',

    author='Haibin Huang',
    author_email='haibin.huang@intel.com',

    url='https://opendev.org/openstack/stevedore',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.5',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=['hpa',
              ],

    packages=find_packages(),
    install_requires=['stevedore'],
    include_package_data=True,

    entry_points={
        'hpa.discovery': [
            'discovery = hpa.hpa_discovery:HPA_Discovery',
        ],
    },

    zip_safe=False,
)
