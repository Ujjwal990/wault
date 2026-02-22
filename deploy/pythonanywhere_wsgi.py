"""
Paste this entire file into PythonAnywhere's WSGI configuration file.
Found at: Web tab → click the WSGI configuration file link
"""
import os
import sys

path = '/home/slingshot/wault'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'wault.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
