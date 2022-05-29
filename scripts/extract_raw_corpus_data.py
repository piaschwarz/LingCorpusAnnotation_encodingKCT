"""A module to extract raw corpus (meta)data.

Functions overview:
    * parse_kct_file: parses a KCT corpus file and builds three dictionaries,
        storing data pertaining to achieved and target layers, as well as metadata.

    * build_kct_text: given a dictionary of tokens, such as the ones returned by
        parse_kct_file for the achieved and target layers, sorts and concatenates
        them to rebuild the original text they were part of. The text is intended
        to be the input of the tokenize function in the target.py module.

Author: Matteo Brivio
"""



import re
from string import punctuation



def parse_kct_file(primary_data):
    """Parses a KCT corpus file and collects achieved_raw, target_raw and
    meta data in a format suitable to be further processed.

    Each opening tag (e.g. \\Kind1-begin) is turned into a key, while the
    following row is stored as its value.
    For achieved and target texts, if the row following the opening tag
    is empty or a carriage return, the entire key-val pair is discarded.
    For meta-data, if the row is empty the assigned value is `None`.

    Args:
        primary_data: a KCT corpus text file.

    Return:
        a tuple, storing three dictionaries: target_raw (tar_dict),
        achieved_raw (ach_dict) and meta data (meta_dict).
    """
    with open(primary_data, "r", encoding="utf-8") as data:
        lines = list(data)
        # store "-begin" lines as keys and the following sentences as values
        data_dict = dict(zip(lines[::3], lines[1::3]))

    is_tar_key = lambda line: bool(re.search(r"(Richtig)\d+(-begin)", line))
    is_ach_key = lambda line: bool(re.search(r"(Kind)\d+(-begin)", line))

    tar_dict = {key.strip("\\\n"): data_dict[key].strip() for key in data_dict.keys()
        if is_tar_key(key) and data_dict[key].strip()}

    ach_dict = {key.strip("\\\n"): data_dict[key].strip() for key in data_dict.keys()
        if is_ach_key(key) and data_dict[key].strip()}

    meta_dict = {key.strip("\\\n"): (data_dict[key].strip() if data_dict[key].strip() else "Not given")
        for key in data_dict.keys() if not (is_tar_key(key) or is_ach_key(key))}

    return tar_dict, ach_dict, meta_dict



def build_kct_text(text_units):
    """Builds a raw string of text out of a dictionary of tokens or sentences.

    Dictionary values are sorted and concatenated according to the integer
    values in their keys (e.g. \\Kind1-begin, Tok1), allowing to retrieve
    the originally elicited achieved/target text.

    Args:
        text_units: a dictionary of tokens or sentences.

    Return:
        a string representing the originally achieved/target text.
    """
    get_int = lambda line: int(*re.findall(r"\d+", line))
    text_raw = " ".join([text_units[k].strip() for k in sorted(text_units.keys(), key=get_int)])

    # fix spaces near punctuation e.g. 'foo , bar' => 'foo, bar'
    text = re.sub(r"\s([!?,.;:%$/\\])", r"\1", text_raw)

    # fix spaces inside of quotes e.g. 'foo " bar " " baz "' => 'foo "bar" "baz"'
    text = re.sub(r"\"\s+(.*?)\s+\"", r'"\1"', text)

    # fix remaining instances of multiple spaces e.g. 'foo   "bar"   "baz"' => 'foo "bar" "baz"'
    text = re.sub(r" {2,}", r" ", text)

    # remove leading and trailing spaces
    text = text.strip()

    return text
