# coding: utf-8
import unittest

from textwrap import dedent

from collections import OrderedDict

from nose.tools import raises

from formpack import FormPack
from formpack.fixtures import build_fixture

import time

a = time.time()

print('Loading fixtures')
title, schemas, submissions = build_fixture('grouped_repeatable')

b = time.time()
print(b - a, 's')

print('Loading schema')
fp = FormPack(schemas, title)

a = time.time()
print(a - b, 's')

options = { }

print('Python export')
export = fp.export(**options)

b = time.time()
print(b - a, 's')


print('xls export')
#export.to_xlsx('/tmp/foo.xlsx', submissions)
#data = export.to_table()
#print(data['submissions'][-1])

for x in export.to_html(submissions):
    print(x)

a = time.time()

print(a - b, 's')
