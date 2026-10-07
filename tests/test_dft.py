from collections import defaultdict

from formpack.schema import FormField
from formpack.utils.dft import dft_recurse

def _create_analysis_fields_tree(survey_field):
    uuids = ['uuid-analysis-q1', 'uuid-analysis-q2']
    xpath = survey_field.path
    analysis_fields = []
    # add QA questions
    for i in range(2):
        q_uuid = uuids[i]
        analysis_fields.append(
            FormField.from_json_definition(
                definition={
                    'label': f'Analysis question {i}?',
                    'source': 'q1',
                    'name': f'q1/{q_uuid}',
                    'type': 'qualInteger',
                    'dtpath': f'{xpath}/{q_uuid}',
                },
                translations=[None],
            )
        )
    # add verification fields
    for i in range(2):
        q_uuid = uuids[i]
        analysis_fields.append(
            FormField.from_json_definition(
                definition={
                    'label': f'Analysis question {i} verification',
                    'source': f'q1/{q_uuid}',
                    'name': f'q1/{q_uuid}/verification',
                    'type': 'qualVerification',
                    'dtpath': f'{xpath}/{q_uuid}/verified',
                },
                translations=[None],
            )
        )
    tree = defaultdict(list)
    for field in analysis_fields:
        tree[field.source].append(field)
    return tree

def test_depth_first_traversal():
    uuids = ['uuid-analysis-q1', 'uuid-analysis-q2']
    survey_field = FormField.from_json_definition(
        definition={
            'type': 'audio',
            '$kuid': 'pq4yg66',
            'label': ['q1'],
            '$xpath': 'q1',
            'required': False,
            'name': 'q1',
        },
        translations=[None],
    )
    analysis_tree = _create_analysis_fields_tree(survey_field)
    all_nodes = dft_recurse(
        root=survey_field, tree=analysis_tree, process_field=lambda x: x
    )
    all_nodes = [node.name for node in all_nodes]
    assert all_nodes == [
        'q1',
        'q1/uuid-analysis-q1',
        'q1/uuid-analysis-q1/verification',
        'q1/uuid-analysis-q2',
        'q1/uuid-analysis-q2/verification',
    ]

def test_depth_first_traversal_handles_cycles():
    survey_field = FormField.from_json_definition(
        definition={
            'type': 'audio',
            '$kuid': 'pq4yg66',
            'label': ['q1'],
            '$xpath': 'q1',
            'required': False,
            'name': 'q1',
        },
        translations=[None],
    )
    analysis_tree = _create_analysis_fields_tree(survey_field)
    # force a circular path
    analysis_tree['q1/uuid-analysis-q1/verification'] = [survey_field]
    all_nodes = dft_recurse(
        root=survey_field, tree=analysis_tree, process_field=lambda x: x
    )
    all_nodes = [node.name for node in all_nodes]
    assert all_nodes == [
        'q1',
        'q1/uuid-analysis-q1',
        'q1/uuid-analysis-q1/verification',
        'q1/uuid-analysis-q2',
        'q1/uuid-analysis-q2/verification',
    ]

def test_dft_with_older_xpaths():
    survey_field = FormField.from_json_definition(
        definition={
            'type': 'audio',
            '$kuid': 'pq4yg66',
            'label': ['q1'],
            '$xpath': 'q1',
            'required': False,
            'name': 'q1',
        },
        translations=[None],
    )
    analysis_tree = _create_analysis_fields_tree(survey_field)
    # simulate the field being moved into a non-repeating group
    new_survey_field = FormField.from_json_definition(
        definition={
            'type': 'audio',
            '$kuid': 'pq4yg66',
            'label': ['q1'],
            '$xpath': 'group1/q1',
            'required': False,
            'name': 'q1',
        },
        translations = [None],
    )
    new_survey_field.add_previous_xpath('q1')
    all_nodes = dft_recurse(
        root=new_survey_field, tree=analysis_tree, process_field=lambda x: x
    )
    all_nodes = [node.name for node in all_nodes]
    assert all_nodes == [
        'q1',
        'q1/uuid-analysis-q1',
        'q1/uuid-analysis-q1/verification',
        'q1/uuid-analysis-q2',
        'q1/uuid-analysis-q2/verification',
    ]
