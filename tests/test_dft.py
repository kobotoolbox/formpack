from collections import defaultdict

from formpack.schema import FormField
from formpack.utils.dft import dft_recurse


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
                    'dtpath': f'q1/{q_uuid}',
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
                    'dtpath': f'q1/{q_uuid}/verified',
                },
                translations=[None],
            )
        )
    tree = defaultdict(list)
    for field in analysis_fields:
        tree[field.source].append(field)
    all_nodes = dft_recurse(
        root=survey_field, tree=tree, process_field=lambda x: x
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
                    'dtpath': f'q1/{q_uuid}',
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
                    'dtpath': f'q1/{q_uuid}/verified',
                },
                translations=[None],
            )
        )
    tree = defaultdict(list)
    for field in analysis_fields:
        tree[field.source].append(field)
    # force a circular path
    tree['q1/uuid-analysis-q1/verification'] = [survey_field]
    all_nodes = dft_recurse(
        root=survey_field, tree=tree, process_field=lambda x: x
    )
    all_nodes = [node.name for node in all_nodes]
    assert all_nodes == [
        'q1',
        'q1/uuid-analysis-q1',
        'q1/uuid-analysis-q1/verification',
        'q1/uuid-analysis-q2',
        'q1/uuid-analysis-q2/verification',
    ]
