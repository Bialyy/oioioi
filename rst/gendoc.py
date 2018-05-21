# Generate documentation script

# This script traverses the main oioioi directory, making an entry
# in modules.rst file for each oioioi module.


from __future__ import print_function

import os
import sys
import oioioi

sections_suff = '../rst/source/sections/'
sections_dist = len(sections_suff.split(os.sep))

entries = []

entries.append("""
Autogenerated by the /rst/gendoc.py script

==============
OIOIOI Modules
==============

List of modules
---------------

""")

oioioi_dirname = os.path.dirname(oioioi.__file__)
sections_dirname = os.path.join(oioioi_dirname, sections_suff)
for root, dirs, files in os.walk(oioioi_dirname):
    dirs.sort()
    rel_root = os.path.relpath(root, sections_dirname)
    module_name = '.'.join(rel_root.split(os.sep)[sections_dist-1:])
    if 'README.rst' in files:
        entries.append('**%s**\n\n.. include:: %s/README.rst\n\n' %
                (module_name, rel_root))
    elif len(rel_root.split(os.sep)) == sections_dist \
            and 'locale' not in module_name:
        print("No README.rst in %s" % module_name)

content = ''.join(entries)

if len(sys.argv) > 1 and (sys.argv[1] == '--verbose' or sys.argv[1] == '-v'):
    print(content)

f = open(os.path.join(oioioi_dirname,
        sections_suff, 'modules.rst'), 'w')
f.write(content)
f.close()
