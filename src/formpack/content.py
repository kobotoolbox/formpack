from a1d05eba1 import (
    BaseContent,
    MAIN_JSONSCHEMA,
    kfrozendict,
    deepfreeze,
    ContentValidationError,
)

from a1d05eba1.transformations.fill_missing_labels import FillMissingLabelsRW

class Content(BaseContent):
    '''
    Match content against a jsonschema

    Formpack assumes that forms used to generate exports have already been
    standardized elsewhere. It will raise a `ContentValidationError` if the
    content does not match
    '''
    schema_string = '2'
    input_schema = MAIN_JSONSCHEMA
    transformers = (
        FillMissingLabelsRW,
    )
