# coding: utf-8
'''
Quotes, newlines, and long URLs: oh, my!

Double quotation marks need to be escaped (by doubling them!) in CSV exports,
    e.g. `Introduce excerpts with "` would become `Introduce excerpts with ""`.

Excel does not tolerate hyperlinks with URLs longer than 255 characters. Not
that we ever explicitly create Excel hyperlinks, but
https://github.com/jmcnamara/XlsxWriter tries to be helpful and add them
automatically. Excessively long URLs should just be written as strings.
'''

DATA = {
    'title': 'Quotes, newlines, and long URLs',
    'id_string': 'quotes_newlines_and_long_urls',
    'versions': [
        {
            "version": "first",
            "content": {
                "choices": [
                    {
                        "label": ["yes"],
                        "list_name": "yes_no",
                        "name": "yes",
                    },
                    {
                        "label": ["no"],
                        "list_name": "yes_no",
                        "name": "no",
                    },
                ],
                "survey": [
                    {
                        "required": False,
                        "appearance": "multiline",
                        "name": "Enter_some_long_text_and_linebreaks_here",
                        "label": [
                            "Enter some long text with \" and linebreaks here"
                        ],
                        "type": "text",
                    },
                    {
                        "select_from_list_name": "yes_no",
                        "required": False,
                        "name": "Some_other_question",
                        "label": ["Some other question"],
                        "type": "select_one",
                    },
                ],
            },
            'submissions': [
                {
                    "Enter_some_long_text_and_linebreaks_here":
                        "Check out this URL I found:\n"
                        "https://now.read.this/?Never%20forget%20that%20you%20"
                        "are%20one%20of%20a%20kind.%20Never%20forget%20that%20"
                        "if%20there%20weren%27t%20any%20need%20for%20you%20in"
                        "%20all%20your%20uniqueness%20to%20be%20on%20this%20"
                        "earth%2C%20you%20wouldn%27t%20be%20here%20in%20the%20"
                        "first%20place.%20And%20never%20forget%2C%20no%20"
                        "matter%20how%20overwhelming%20life%27s%20challenges"
                        "%20and%20problems%20seem%20to%20be%2C%20that%20one%20"
                        "person%20can%20make%20a%20difference%20in%20the%20"
                        "world.%20In%20fact%2C%20it%20is%20always%20because%20"
                        "of%20one%20person%20that%20all%20the%20changes%20that"
                        "%20matter%20in%20the%20world%20come%20about.%20So%20"
                        "be%20that%20one%20person.",
                    "Some_other_question": "yes",
                },
                # Thanks to @tinok for the whimisical sample data below
                {
                    "Enter_some_long_text_and_linebreaks_here":
                        "Hi, my name is Roger.\"\n\nI like to enter quotes "
                        "randomly and follow them with new lines.",
                    "Some_other_question": "yes",
                },
                {
                    "Enter_some_long_text_and_linebreaks_here":
                        "This one has no linebreaks",
                    "Some_other_question": "no",
                },
                {
                    "Enter_some_long_text_and_linebreaks_here":
                        "This\nis\nnot\na Haiku",
                    "Some_other_question": "yes",
                },
                {
                    "Enter_some_long_text_and_linebreaks_here":
                        "\"Hands up!\" He yelled.\nWhy?\"\nShe couldn't "
                        "understand anything.",
                    "Some_other_question": "yes",
                },
            ],
        },
    ],
}
