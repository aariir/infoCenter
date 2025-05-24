from setuptools import setup

APP = ['src/app.py']
DATA_FILES = []
OPTIONS = {
    'includes': [
        'rumps',
        'psutil',
        'requests',
        'urllib3',
        'certifi',
        'chardet',
        'idna',
        'json',
        'os',
        'sys',
        'socket',
        'jaraco.text',
        'pkg_resources'
    ],
    'argv_emulation': False,
    'packages': [],
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'InfoCenter',
        'CFBundleDisplayName': 'InfoCenter',
        'CFBundleIdentifier': 'io.iiroaarn.infoCenter',
        'CFBundleVersion': '0.1.1',
        'CFBundleShortVersionString': '0.1.1',
        'LSUIElement': True,
    },
}

setup(
    app=APP,
    name='InfoCenter',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)