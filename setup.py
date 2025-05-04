from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tamir_atolyesi",
    version="1.0.0",
    author="Mehmet Said ÖZSOY",
    author_email="support@tamiratolyesi.com",
    description="Tamir Atölyesi Yönetim Sistemi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mehmetsaidozsoy/tamir-atolyesi",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Natural Language :: Turkish",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tamir_atolyesi=tamir_atolyesi.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "tamir_atolyesi": [
            "icons/*.png",
            "icons/*.ico",
            "data/*.db",
            "locale/*/LC_MESSAGES/*.mo",
            "fonts/*.ttf",
            "gui/*.py",
            "web-ui/*",
            "models/*.py",
            "database/*.py",
            "utils/*.py",
            "backup/*.py",
            "config/*.py",
        ],
    },
    data_files=[
        ("share/applications", ["debian/tamir-atolyesi.desktop"]),
        ("share/icons/hicolor/48x48/apps", ["icons/tamir-atolyesi.png"]),
        ("share/icons/hicolor/256x256/apps", ["icons/tamir-atolyesi.png"]),
        ("share/tamir_atolyesi/data", ["tamir_atolyesi.db"]),
        ("share/tamir_atolyesi/fonts", ["DejaVuSans.ttf"]),
    ],
) 