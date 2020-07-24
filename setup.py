from setuptools import find_packages, setup

install_requires = ["python-telegram-bot", "python-magic", "lottie", "cairosvg"]

tests_require = []


setup(
    name="telegram_broker",
    version="0.1.2",
    description="Telegram broker for Odoo",
    long_description="Telegram broker for Odoo",
    author="Enric Tobella Alomar",
    author_email="etobella@creublanca.es",
    url="http://github.com/tegin/telegram-broker",
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={"test": tests_require},
    entry_points={},
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    zip_safe=False,
)
