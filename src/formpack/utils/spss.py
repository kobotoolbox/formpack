# -*- coding: utf-8 -*-
# 😬

from __future__ import unicode_literals
from collections import OrderedDict

# Constants
LINE_LIMIT_BYTES = 251
VARIABLE_LABEL_LIMIT_BYTES = 255
VALUE_LABEL_LIMIT_BYTES = 120
SELECT_MULTIPLE_NAME_DELIMITER = '_'
SELECT_MULTIPLE_LABEL_DELIMITER = ' :: '
''' SPSS limits variable names to 64 bytes, but we'll create more problems for
people if we try to change variable names here. Any change to them would
require altering data exports as well; otherwise, the labels we generate would
be useless '''
VARIABLE_NAME_LIMIT_BYTES = 64


# HELPERS --------------------------

# https://stackoverflow.com/questions/30686701/python-get-size-of-string-in-bytes
def utf8_len(s):
    return len(s.encode('utf-8'))

def spss_escape(s):
    return s.replace("'", "''").replace("\n", "\\n")

def utf8_ellipsize(s, max_bytes, ellipsis='…'):
    r"""
    If necessary, truncate the string `s` and concatenate the result with
    `ellipsis` such that the final string length does not exceed `max_bytes`
    :Example:
        >>> utf8_ellipsize('These 🐿🐿 have taken too many bytes!',
        ...                max_bytes=37)
        'These 🐿🐿 have taken too many…'
    """

    if utf8_len(s) <= max_bytes:
        return s

    ellipsis_bytes = utf8_len(ellipsis)
    if max_bytes < ellipsis_bytes:
        raise Exception(
            '`max_bytes` cannot be less than the length in bytes of `ellipsis`'
        )

    for slice_end in range(len(s), -1, -1):
        candidate = s[:slice_end]
        if utf8_len(candidate) + ellipsis_bytes <= max_bytes:
            return candidate + ellipsis

    raise Exception('It should be impossible to get here :)')


def spss_labels_from_variables_dict(variables):
    # Create initial version of each section, no wrapping
    variable_section_lines = ['VARIABLE LABELS']
    value_section_lines = ['VALUE LABELS']
    variable_count = 0 # because the first does not need a leading slash
    value_count = 0

    for variable_name, variable in variables.items():
        if utf8_len(variable_name) > VARIABLE_NAME_LIMIT_BYTES:
            logging.warning(
                'SPSS variable name exceeds {} bytes: {}'.format(
                    VARIABLE_NAME_LIMIT_BYTES,
                    variable_name
            ))

        variable_section_lines.append(
            "{line_leader}{variable_name} '{variable_label}'".format(
                line_leader=' /' if variable_count else ' ',
                variable_name=variable_name,
                variable_label=spss_escape(
                    utf8_ellipsize(
                        variable['label'],
                        VARIABLE_LABEL_LIMIT_BYTES,
                )))
        )
        variable_count += 1

        try:
            values = variable['values']
        except KeyError:
            continue

        # For select multiple questions, generate an additional variable
        # label for each choice, using the format
        #     question_name_choice_name 'question label :: choice label'
        #                  ^ a literal underscore
        # TODO: advise people to export data using `_` as the group delimiter,
        # since the default, `/`, is not allowed by SPSS
        if variable['data_type'] == 'select_multiple':
            for value_name, value_label in values.items():
                label_format_string = '{variable_label}{delimiter}{value_label}'
                output = label_format_string.format(
                    variable_label=variable['label'],
                    delimiter=SELECT_MULTIPLE_LABEL_DELIMITER,
                    value_label=value_label
                )
                if utf8_len(output) > VARIABLE_LABEL_LIMIT_BYTES:
                    variable_label = utf8_ellipsize(
                        variable['label'], int(VARIABLE_LABEL_LIMIT_BYTES / 2)
                    )
                    value_label = utf8_ellipsize(
                        value_label,
                        VARIABLE_LABEL_LIMIT_BYTES - utf8_len(variable_label) -
                            utf8_len(SELECT_MULTIPLE_LABEL_DELIMITER)
                    )
                    output = label_format_string.format(
                        variable_label=variable_label,
                        delimiter=SELECT_MULTIPLE_LABEL_DELIMITER,
                        value_label=value_label
                    )
                assert utf8_len(output) <= VARIABLE_LABEL_LIMIT_BYTES
                variable_section_lines.append(
                    "{line_leader}{variable_name}{delimiter}{value_name} "
                    "'{variable_label}'".format(
                        line_leader=' /' if variable_count else ' ',
                        variable_name=variable_name,
                        delimiter=SELECT_MULTIPLE_NAME_DELIMITER,
                        value_name=value_name,
                        variable_label=spss_escape(output)
                    )
                )
                variable_count += 1
            # Don't add any SPSS value labels
            continue

        value_section_lines.append(
            "{line_leader}{variable_name}".format(
                line_leader=' /' if value_count else ' ',
                variable_name=variable_name,
            )
        )
        for value_name, value_label in values.items():
            value_section_lines.append(
                " '{value_name}' '{value_label}'".format(
                    value_name=spss_escape(value_name),
                    value_label=spss_escape(
                        utf8_ellipsize(value_label, VALUE_LABEL_LIMIT_BYTES)
                    )
                )
            )
        value_count += 1

    variable_section_lines.append(' .')
    value_section_lines.append(' .')
    full_file_lines = variable_section_lines + value_section_lines

    # Wrap long strings into multiple lines, where possible
    line_no = 0
    while line_no < len(full_file_lines):
        line = full_file_lines[line_no]
        if utf8_len(line) > LINE_LIMIT_BYTES:
            # coerce unicode string to list of codes for iteration
            chars = list(line)
            # Iterating over chars, keeping a best split point, to wrap within
            # the byte limits. Chars might be multiple unicode bytes together,
            # which we don't want to split between lines.
            char_i = 0
            in_string = False
            last_split = 0
            last_split_in_string = False
            line_limit = LINE_LIMIT_BYTES # this will change if in a string
            byte_count = 0
            while (byte_count < line_limit):
                # good split points: whitespace, or good insides of strings
                char = chars[char_i]
                if in_string:
                    # handle `\n` and `''`
                    bichar = ''.join(chars[char_i:char_i+2])
                    if bichar == '\\n' or bichar == "''":
                        last_split = char_i
                        last_split_in_string = True
                        # advance extra
                        char_i += 1
                        byte_count += 1
                    else:
                        if char == "'":
                            in_string = False; line_limit += 1
                        else:
                            last_split = char_i
                            last_split_in_string = True
                else:
                    if char == "'":
                        in_string = True; line_limit -= 1
                    if char == " ":
                        last_split = char_i
                        last_split_in_string = False
                char_i += 1
                byte_count += len(char.encode('utf-8'))
            if last_split == 0:
                raise Exception("Can't split line {}".format(line_no))
            else:
                if last_split_in_string:
                    next_line = (" + '" + line[last_split:])#.rstrip()
                    line = full_file_lines[line_no] = line[0:last_split] + "'"
                    full_file_lines.insert(line_no + 1, next_line)
                else:
                    # print "split outside of string." + line
                    next_line = (" " + line[last_split:])#.rstrip()
                    line = full_file_lines[line_no] = line[0:last_split]#.rstrip()
                    full_file_lines.insert(line_no + 1, next_line)
        line_no += 1

    # Use CRLF line endings because that's what SPSS does when saving (at least
    # on Windows!)
    return '\r\n'.join(full_file_lines)
