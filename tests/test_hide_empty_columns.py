# coding: utf-8
from zipfile import ZipFile
from path import TempDir

import openpyxl

import pytest
import pyxform
from formpack import FormPack

from .fixtures import build_fixture

# xml representation of a hidden column shows up in unzipped xlsx file:
HIDDEN_ATTR = ' hidden="1"'


def _modified_fixture():
    title, schemas, submissions = build_fixture('favorite_coffee')
    for schema in schemas:
        schema['content']['survey'].append({
            'type': 'text',
            'label': ['This field will not have any submitted data'],
            'name': 'blank',
            'required': False,
        })
    for submission in submissions:
        submission['blank'] = ''
    return (title, schemas, submissions)


def test_normal_export():
    """
    a simple XLSX export test that
    would fail if param: hide_unused=True
    were passed to fp.export(...)
    """
    title, schemas, submissions = _modified_fixture()
    fp = FormPack(schemas, title)
    export_params = {'versions': fp.versions.keys()}

    with TempDir() as d:
        xlsx_path = d / 'hide_unused_false.xlsx'
        fp.export(**export_params).to_xlsx(xlsx_path, submissions)
        with open(xlsx_path, 'rb') as ff:
            workbook = openpyxl.load_workbook(ff)
            sheet1 = workbook[workbook.sheetnames[0]]
            columns = [cell.value for cell in sheet1[1]]
            vals1 = [cell.value for cell in sheet1[2]]
            assert 'blank' in columns
        # assert that there is NO hidden column in the xlsx
        with ZipFile(xlsx_path) as zip:
            with zip.open('xl/worksheets/sheet1.xml') as ff:
                assert HIDDEN_ATTR not in str(ff.read())


def test_export_with_hide_unused_true():
    """
    similar to "test_normal_export" but
    param: hide_unused=True
    leads to a slightly different resulting XLSX
    """
    title, schemas, submissions = _modified_fixture()
    fp = FormPack(schemas, title)
    export_params = {'versions': fp.versions.keys()}

    # kwarg passed to fp.export(...) to trigger this behavior
    export_params['hide_unused'] = True

    with TempDir() as d:
        xlsx_path = d / 'hide_unused_true.xlsx'
        fp.export(**export_params).to_xlsx(xlsx_path, submissions)
        # assert that there's a hidden column in the xlsx
        with ZipFile(xlsx_path) as zip:
            with zip.open('xl/worksheets/sheet1.xml') as ff:
                # hidden_column looks like this in the xlsx
                # <col min="7" max="7" width="0" hidden="1" customWidth="1"/>
                assert HIDDEN_ATTR in str(ff.read())
