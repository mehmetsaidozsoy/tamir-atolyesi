from setuptools import setup, find_packages

setup(
    name="tamir_atolyesi",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'fpdf2==2.7.6',
        'tkcalendar==1.6.1',
        'pandas==2.2.0',
        'openpyxl==3.1.2',
        'schedule==1.2.1',
        'pillow==11.2.1',
    ],
    entry_points={
        'console_scripts': [
            'tamir_atolyesi=main:main',
        ],
    },
    package_data={
        'tamir_atolyesi': ['DejaVuSans.ttf', 'icon.ico'],
    },
    author="Mehmet Said Özsoy",
    author_email="mehmetsaidozsoy@gmail.com",
    description="Tamir Atölyesi Yönetim Sistemi",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="tamir atolye yonetim sistem",
    url="",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business",
    ],
) 