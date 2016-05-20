# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
grouped questions:

has some boring questions in a group

'''

DATA = {
    u'title': 'Grouped questions',
    u'id_string': 'grouped_questions',
    u'versions': [
        {
            'version': 'gqs',
            'content': {
                'survey': [
                    {
                        'type': 'text',
                        'name': 'q1',
                        'label': 'Q1'
                    },
                    {
                        'type': 'begin  group',
                        'name': 'g1',
                        'label': 'Group 1',
                    },
                    {
                        'type': 'text',
                        'name': 'g1q1',
                        'label': 'G1Q1'
                    },
                    {
                        'type': 'begin group',
                        'name': 'sg1',
                        'label': 'Sub Group 1',
                    },
                    {
                        'type': 'text',
                        'name': 'g1sg1q1',
                        'label': 'G1SG1Q1'
                    },
                    {
                        'type': 'end group',
                    },
                    {
                        'type': 'text',
                        'name': 'g1q2',
                        'label': 'G1Q2'
                    },
                    {
                        'type': 'end  group',
                    },
                    {
                        'type': 'begin group',
                        'name': 'g2',
                        # no label here on purpose.
                        # not all groups have labels
                    },
                    {
                        'type': 'text',
                        'name': 'g2q1',
                        'label': 'G2Q1'
                    },
                    {
                        'type': 'end group',
                    },
                    {
                        'type': 'text',
                        'name': 'qz',
                        'label': 'QZed'
                    },
                ]
            },
            'submissions': [
                # this is more-or-less how the data is stored in mongo
                # but we can also hypothesize on ideals
                {
                    'q1': 'respondent1\'s r1',
                    'g1/g1q1': 'respondent1\'s r2',
                    'g1/sg1/g1sg1q1': 'respondent1\'s r2.5',
                    'g1/g1q2': 'respondent1\'s r2.75 :)',
                    'g2/g2q1': 'respondent1\'s r3',
                    'qz': 'respondent1\'s r4',
                },
                {
                    'q1': 'respondent2\'s r1',
                    'g1/g1q1': 'respondent2\'s r2',
                    'g1/sg1/g1sg1q1': 'respondent2\'s r2.5',
                    'g1/g1q2': 'respondent2\'s r2.75 :)',
                    'g2/g2q1': 'respondent2\'s r3',
                    'qz': 'respondent2\'s r4',
                }
            ],
        }
    ],
}
