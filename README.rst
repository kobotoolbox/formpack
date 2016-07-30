formpack: machinery to build and export reports for kobocat data
================================================================

Installing
----------

::

    $ virtualenv ../formpack_virtualenv
    $ source ../formpack_virtualenv/bin/activate
    (formpack_virtualenv) $ easy_install six Jinja2
    (formpack_virtualenv) $ git clone https://github.com/kobotoolbox/formpack.git
    (formpack_virtualenv) $ cd formpack/
    (formpack_virtualenv) $ python setup.py develop (or install)

Testing
~~~~~~~

::

    (formpack_virtualenv) $ easy_install pytest nose
    (formpack_virtualenv) $ py.test -sx

test session starts
'''''''''''''''''''

collected 62 items

tests/test\_array\_to\_xpath.py …………..

tests/test\_autoreport.py …

tests/test\_expand\_content.py …………

tests/test\_exports.py …………..

tests/test\_fixtures\_valid.py …..

tests/test\_formpack\_attachments.py …

tests/test\_formpack\_internals.py .

tests/test\_invalid\_structures.py ….

tests/test\_utils.py ……

62 passed in 0.34 seconds
'''''''''''''''''''''''''

Using
-----

Command line methods

::

    python -m formpack xls example.xlsx # convert xlsx file to json
