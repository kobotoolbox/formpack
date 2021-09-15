# coding: utf-8
"""
formpack.pack.FormPack

A FormPack object pulls data associated with a single form or a multi-versioned
form and parses it.

A FormPack loaded with project data can be restructured and analysed by a
separate utility.

This module is intended to store data collected by the full range of features
of the ODK-flavored XForms including:
 * translated forms
 * media attachments
 * complex data types
"""

from .pack import FormPack
