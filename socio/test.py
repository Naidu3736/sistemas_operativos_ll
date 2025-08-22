# check_icons_file.py
import inspect
from flet.core import icons

print("Archivo de íconos:", inspect.getfile(icons))
print("Contenido del módulo icons:")
print([x for x in dir(icons) if not x.startswith('_')])