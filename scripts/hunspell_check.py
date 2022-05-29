"""
Author: Matteo Brivio
"""

import hunspell
import pprint
from string import punctuation


def spell_check(toks, silent=True, de_dic=None, de_aff=None):
    """Provides basic assistance with spell-checking each token
    in the given dictionary. If potentially mispelled words are
    found, the correction can be performed either automatically
    or manually. At the end, the original dictionary is updated
    with the corrected values.

    The function relies on pyhunspell, a set of Python bindings
    for the Hunspell spellchecker engine.
    (https://github.com/blatinier/pyhunspell)

    Args:
        toks: a dictionary storing word tokens e.g. `{tok0:lesen}`.
        silent: boolean flag. If True, the script runs silently and
            potential mistakes are automatically corrected without
            notifying the user.
        de_dic: path to the hunspell German dic file.
        de_aff: path to the hunspell German aff file.

    Returns:
        a dictionary storing word tokens.
    """
    # prompt messages to the user
    auto_correct_prompt = "Type 1 to run automatic correction, 0 for manual: "
    correcting_prompt = "Type 1 to cancel the output, 0 to save it: "
    correction_prompt = "Type a new value or hit ENTER to keep the current one: "

    # instantiate checker and load dictionaries
    checker = hunspell.HunSpell(de_dic, de_aff)

    # build a dictionary of potentially mispelled tokens
    is_valid = lambda token: not (token in punctuation or token.isnumeric())
    mispelled = {k: v for k, v in toks.items() if is_valid(v) and not checker.spell(v)}

    correcting = True

    while mispelled and correcting:
        if not silent:
            print(f"Potentially mispelled words found: {len(mispelled)}")
            pprint.pprint(mispelled)

        auto_correct = int(input(auto_correct_prompt)) if not silent else 1

        if auto_correct:
            # get the best suggestion for each word or keep the word
            guess = lambda word: checker.suggest(word)
            mispelled = {k: ((guess(v) and guess(v)[0]) or v) for k, v in mispelled.items()}

            if not silent:
                print("Output corrections:")
                pprint.pprint(mispelled)

            correcting = int(input(correcting_prompt)) if not silent else 0

        else:
            for k, v in mispelled.items():
                print("misspelled:", v)
                print("suggestion:", checker.suggest(v))
                correction = input(correction_prompt)
                mispelled[k] = correction if correction else v

            print("Output corrections:")
            pprint.pprint(mispelled)

            correcting = int(input(correcting_prompt))

        toks.update(mispelled)
