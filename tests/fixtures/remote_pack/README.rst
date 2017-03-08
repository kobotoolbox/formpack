This directory provides an `__init__.py` file which can be put in the same
directory as a backup of production data via the remote_pack.py CLI utility

Simply copy or move the directory containing data (example: "~/.formpack/aFoRmId654321")
to the parent directory "tests/fixtures" and copy the accompanying `__init__.py`
file. The data can then be tested with formpack through the "build_fixtures(...)"
method.
