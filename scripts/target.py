"""
Author: Pia Schwarz

This script contains methods to process the 'target' and 'achieved' text:
-------------------------------------------------------
function to tokenize sentence, storing tokens into a list;
    Er war glücklich und{2} war in_der Bücherei jeden Tag und freute si§ch,
    [Er, war, glücklich, und{2}, war, in_der, …, si§ch, ,]

function to remove/resolve annotation symbols from output of function 3;
    Input to the function: [Er, war, glücklich, und{2}, war, in_der, … si§ch, ,]
    {tok1:Er, tok2:war, tok3:glücklich, tok4:und, ..., tokx:in, toky:der, … si§ch, ,}
    {span1:tok1, span2:tok2, …, span4:tok4, span6: [tokx, toky], ...}
    {span4:{2}, span6:_, spann:§}
-------------------------------------------------------

"""

import re

"""
    Reads a string and tokenizes this text into a list of strings.
    Tokenization is done mainly through separating at white space, tokenizing punctuation as separate items
    and considering special annotation symbols.
    
    Example
        Input text: "und dann haben [§ sie] ihn aufgenommen und dann war er auch ein kultivierter Wolf.
                    Er war glücklich und{2} war in_der Bücherei"
        Output list: [und, dann, haben, [§ sie], ihn, aufgenommen, und, dann, war, er, auch, ein, kultivierter, Wolf, .,
                    Er, war, glücklich, und{2}, war, in_der, Bücherei]
                    
    :arg file: the txt file to tokenize
    :returns: List of string items corresponding to the single tokens    
"""
def tokenize(text):  # def tokenize(file):

    #with open(file, 'r', encoding="utf-8") as reader:
    #    text = "".join(reader)


    # separate punctuation (. , : ? ! &#34; standing for ") attached to word with a space
    # (e.g. 'weitergehen.' --> 'weitergehen .')
    # Difficult case (not yet handled): z.§B. Currently split into: 'z', '.', '§B', '.'
    text = re.sub(r'\.', ' . ', text)
    text = re.sub(r',', ' , ', text)
    text = re.sub(r':', ' : ', text)
    text = re.sub(r'\?', ' ? ', text)
    text = re.sub(r'!', ' ! ', text)
    text = re.sub(r'\(', '( ', text)
    text = re.sub(r'\)', ' )', text)

    # now also an occurrence like [. ,] looks like this [ .   , ]
    # or                          [§ .] looks like this [§  . ]
    # but it has to be joined back together (left side of the bracket):
    text = re.sub(r'\[ *\.', '[. ', text)
    text = re.sub(r'\[ *,', '[, ', text)
    text = re.sub(r'\[ *:', '[: ', text)
    text = re.sub(r'\[ *\?', '[? ', text)
    text = re.sub(r'\[ *!', '[! ', text)
    # but it has to be joined back together (right side of the bracket):
    text = re.sub(r'\. *\]', ' .]', text)
    text = re.sub(r', *\]', ' ,]', text)
    text = re.sub(r': *\]', ' :]', text)
    text = re.sub(r'\? *\]', ' ?]', text)
    text = re.sub(r'! *\]', ' !]', text)

    # quotation marks are not correctly encoded (represented as &#34;)
    text = re.sub(r'&#34;', ' " ', text)

    # Join back occurrences like . _B into ._B and . _" into ._"
    text = re.sub(r', _', ',_', text)
    text = re.sub(r'\. _', '._', text)
    text = re.sub(r'" _', '"_', text)
    text = re.sub(r': _', ':_', text)
    text = re.sub(r'_ ,', '_,', text)
    text = re.sub(r'\._ "', '._"', text)
    text = re.sub(r':_ "', ':_"', text)
    text = re.sub(r'_Dann', 'Dann', text)
    text = re.sub(r',_ Dort', ',_Dort', text)
    text = re.sub(r'\._ Tim', '._Tim', text)
    text = re.sub(r'/\[', ' / [', text)
    text = re.sub(r'Ente\[', 'Ente [', text)
    text = re.sub(r'bei\[', 'bei [', text)
    text = re.sub(r'denn\[', 'denn [', text)
    text = re.sub(r'du\[', 'du [', text)
    text = re.sub(r'weglaufen\[', 'weglaufen [', text)
    text = re.sub(r'würde\[', 'würde [', text)
    text = re.sub(r'fern\[sehn §]', 'fern [sehn §]', text)
    text = re.sub(r'ein\[,', 'ein [,', text)
    text = re.sub(r'\[§/]', '[§ /]', text)

    # now split at white space
    tokenized = text.split()

    # join element with next element in the list if it has an opening bracket (e.g. '[§' + 'sie]'
    # this leaves the next element untouched in the list so the next element has to be removed at a later step
    for i in range(len(tokenized)):
        if "[" in tokenized[i]:
            tokenized[i] = tokenized[i] + " " + tokenized[i+1]
            # care for cases like: [i in]_[em den] ; Wie_[s heißt]_der
            if "[" in tokenized[i+1]:
                tokenized[i] = tokenized[i] + " " + tokenized[i + 2]

    # remove all elements that have a closing bracket without opening bracket (e.g. 'sie]'
    for i in tokenized:
        if i.count("[") != i.count("]"):
            tokenized.remove(i)

    # do a second round: remove all elements that have a closing bracket without opening bracket (e.g. 'sie]'
    for i in tokenized:
        if i.count("[") != i.count("]"):
            tokenized.remove(i)

    return tokenized


"""
    USED TO CREATE THE NORMALIZED TEXT OF THE 'TARGET' LAYER
    Creates tok dict (normalized strings), span dict, annotation dict by resolving error annotation symbols
    
    Example
        Input list: [Er, war, glücklich, und{2}, war, in_der, … si§ch, ,]
        Output dicts: -tok dict {tok1:Er, tok2:war, tok3:glücklich, tok4:und, ..., tokx:in, toky:der, … si§ch, ,}
                      -span dict {span1:tok1, span2:tok2, …, span4:tok4, span5:tok5, span6: [tokx, toky], ...}
                      -error dict {span4:{2}, span6:_, spann:§}
                      
    :arg token_list: a list of tokens
    :return: tok dict, span dict, error dict
    
    # delete *                                                     ANNOTATION: *                                              
    # delete §                                                     ANNOTATION: §
    # exchange = with -                                            ANNOTATION: =
    # delete --                                                    ANNOTATION: --
    # delete {number} / {F} / {G} / {N}                            ANNOTATION: {number} / {F} / {G} / {N}
    
    # delete ~ or make two tokens out of it, depends on the case   ANNOTATION: ~
    # detect _ and make two tokens out of it                       ANNOTATION: _
    
    # replace [§ b] with b                                         ANNOTATION: [§ b]
    # replace [a §] with a                                         ANNOTATION: [a §]
    # replace [a b] with b, e.g. replace [seine ihre] with ihre    ANNOTATION: [a b]
    # replace [§ fehlendeswort] with fehlendeswort                 ANNOTATION: [§ fehlendeswort]
    # replace [a *] with a                                         ANNOTATION: [a *]
    
    # Multiple annotations in one token item -> list with multiple items, e.g. {F}, ~, _, {F} for Champions{F}~_league{F}
    
    
    INSTANCES OF TILDE SYMBOL IN KCT (NONE IN H2)
    i~Phone{N}
    Model~job{F}
    i~Pads{F}
    e~bay{F}
    King{N}~Kong{N} ==> King Kong (make two tokens)
    Technik~sachen
    Null~Kalorien ==> Null Kalorien (make two tokens)
    Verkehrs~mittel
    Klamotten~laden
    Roboter~hunde
    3~Mal ==> 3 Mal (make two tokens)
    Champions{F}~_league{F} ==> Champions League (make two tokens)
    Geschindig~keit
    
"""
def create_tok_span_anno_target(token_list):

    tok = dict()
    span = dict()
    anno = dict()

    count_tok_insertions = 0  # always increase by 1 if a token is split into two tokens, e.g. in_der --> in der
    for count, item in enumerate(token_list):

        # first deal with all letter- and word-level annotations
        if "[" not in item:

            # handle special case 'z._B.'
            if item == "_B" or item == "_Karten":
                current_tok_key = "tok" + str(count + count_tok_insertions)
                tok[current_tok_key] = item[1:]

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key
                anno[current_span_key] = ["_"]
                continue

            # handle special case of words consisting only of *
            if all(c == "*" for c in item):
                current_tok_key = "tok" + str(count + count_tok_insertions)
                tok[current_tok_key] = item

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key
                anno[current_span_key] = ["*"]
                continue

            # if item is {N}/{F}/{G} do not create new token
            if item == "{N}" or item == "{F}" or item == "{G}": 
                count_tok_insertions -= 1
                continue

            # handle all symbols which are deleted or exchanged to get the normalized token: * § -- = {n} {F} {G} {N}
            symbols = re.findall('(\*)|(§)|(--)|(=)|({.})', item)

            symbol_underscore = re.findall('_', item)
            symbol_tilde = re.findall('~', item)

            if len(symbols) > 0:
                # now search for symbols again including ~ --> this way the following cases that have two
                # word level annotation symbols in a single word are included, e.g.: i~Phone{N} ; Model~job{F}
                symbols = re.findall('(\*)|(§)|(--)|(=)|({.})|(~)', item)

                symbol_list = []  # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                for i in symbols:
                    for j in i:
                        if len(j) > 0:
                            symbol_list.append(j)

                current_tok_key = "tok" + str(count + count_tok_insertions)

                item_nostar = re.sub(r'\*', '', item)
                item_nopgf = re.sub(r'§', '', item_nostar)
                item_nodoubledash = re.sub(r'--', '', item_nopgf)
                item_noequals = re.sub(r'=', '-', item_nodoubledash)
                item_nocurly = re.sub(r'\{.\}', '', item_noequals)
                item_normalized = re.sub(r'~', '', item_nocurly)


                tok[current_tok_key] = item_normalized

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key
                anno[current_span_key] = symbol_list

            else:  # it's a normal token without any annotation symbol
                current_tok_key = "tok" + str(count + count_tok_insertions)
                tok[current_tok_key] = item

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key


            # found underscore at this item:  zu_lesen
            # found underscore at this item:  vor_allem
            # found underscore at this item:  in_die
            # found underscore at this item:  es_wis--sen{2}
            # found underscore at this item:  Champions{F}~_league{F}
            if len(symbol_underscore) > 0:
                if item == "Champions{F}~_league{F}":
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    item_a_normalized = "Champions"
                    item_b_normalized = "League"

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                    if current_span_key in anno:
                        anno[current_span_key].append('~')
                        anno[current_span_key].append('_')
                    else:
                        anno[current_span_key] = ['~', '_']

                # Handle cases with multiple underscores: Hast_du_es{G}  Danach*_hoffte_der  Pikachu{N}_vs_Raichu{N}_vs_Pichu{N}
                elif len(symbol_underscore) > 1:

                    symbols = re.findall('(\*)|(§)|(--)|(=)|({.})|(~)|(_)', item)
                    symbol_list = []  # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                    for i in symbols:
                        for j in i:
                            if len(j) > 0:
                                symbol_list.append(j)

                    item_list = item.split('_')
                    span_list = []
                    for i in item_list:
                        item_nostar = re.sub(r'\*', '', i)
                        item_nopgf = re.sub(r'§', '', item_nostar)
                        item_nodoubledash = re.sub(r'--', '', item_nopgf)
                        item_noequals = re.sub(r'=', '-', item_nodoubledash)
                        item_nocurly = re.sub(r'\{.\}', '', item_noequals)
                        item_normalized = re.sub(r'~', '', item_nocurly)

                        current_tok_key = "tok" + str(count + count_tok_insertions)
                        count_tok_insertions = count_tok_insertions + 1
                        tok[current_tok_key] = item_normalized
                        span_list.append(current_tok_key)

                    count_tok_insertions = count_tok_insertions - 1
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = span_list
                    anno[current_span_key] = symbol_list

                else:
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)

                    item_nostar = re.sub(r'\*', '', item)
                    item_nopgf = re.sub(r'§', '', item_nostar)
                    item_nodoubledash = re.sub(r'--', '', item_nopgf)
                    item_noequals = re.sub(r'=', '-', item_nodoubledash)
                    item_normalized = re.sub(r'\{.\}', '', item_noequals)

                    item_a_normalized = item_normalized.split('_')[0]
                    item_b_normalized = item_normalized.split('_')[1]

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                    if current_span_key in anno:
                        anno[current_span_key].append('_')
                    else:
                        anno[current_span_key] = ['_']

            # SPECIAL CASES:
            # found tilde at this item:  Null~Kalorien
            # found tilde at this item:  King{N}~Kong{N}
            # found tilde at this item:  Champions{F}~_league{F} --> this case is already handled!
            # found tilde at this item:  3~Mal
            if len(symbol_tilde) > 0:
                if item in ["Null~Kalorien", "King{N}~Kong{N}", "3~Mal"]:
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)

                    item_nostar = re.sub(r'\*', '', item)
                    item_nopgf = re.sub(r'§', '', item_nostar)
                    item_nodoubledash = re.sub(r'--', '', item_nopgf)
                    item_noequals = re.sub(r'=', '-', item_nodoubledash)
                    item_normalized = re.sub(r'\{.\}', '', item_noequals)

                    item_a_normalized = item_normalized.split('~')[0]
                    item_b_normalized = item_normalized.split('~')[1]

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                    if current_span_key in anno:
                        anno[current_span_key].append('~')
                    else:
                        anno[current_span_key] = ['~']

        # then deal with all sentence-level annotations (items that do contain "[")
        else:
            # replace [§ b] with b                                         ANNOTATION: [§ b]
            # delete [a §] (a is an unnecessary insertion)                 ANNOTATION: [a §]
            # replace [a b] with b, e.g. replace [seine ihre] with ihre    ANNOTATION: [a b]
            # replace [§ fehlendeswort] with fehlendeswort                 ANNOTATION: [§ fehlendeswort]
            # replace [a *] with a                                         ANNOTATION: [a *]
            # also take care of letter annotation inside words in the brackets, e.g.: [wi - - * en wissen], [*e* sie]


            # first, handle simple cases like listed above (token with single []-bracket and first and last char are [ / ]
            if item.count("[") == 1 and item[0] == '[' and item[-1] == ']':

                first = item.split()[0]
                second = item.split()[1]

                current_tok_key = "tok" + str(count + count_tok_insertions)

                if '§' in second:  # [sahen §] --> [[sahen, §]] --> [sahen --> sahen
                    # no entry in any dict
                    count_tok_insertions = count_tok_insertions - 1
                    continue
                elif '§' in first:  # [§ fehlendeswort] --> [[§, fehlendeswort]] --> fehlendeswort] --> fehlendeswort
                    tok[current_tok_key] = second[:len(second) - 1]
                elif '*' in second:  # replace [a *] with a (check again in paper what this means)
                    tok[current_tok_key] = first[1:]
                else:  # replace [seine ihre] with ihre
                    tok[current_tok_key] = second[:len(second) - 1]

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key
                anno[current_span_key] = [item]  # add full item, e.g [§ fehlendeswort]

            # then take care of complicated cases:
            # DONE: Notfall[. §]_geld
            # DONE: Tag_[machen §] --> make 1 token
            # DONE: vor_[stellen §] --> make 1 token
            # DONE: [i in]_[em den] --> make two tokens
            # DONE: Und_[an dann] --> make two tokens
            # DONE: [*eb lebt]_er{G} --> make two tokens
            # DONE: [zu nach]_Hause --> make two tokens
            # DONE: [s*b* zu]_finden --> make two tokens
            # DONE: alt_aus[§ sahen] --> make two tokens
            # DONE: rein§[§ kommt] --> make 1 token
            # DONE: [§ irgend]wohin --> make 1 token

            else:
                # SPECIAL CASE: this is wrongly annotated, it should be: Notfall[. §]§geld
                if 'Notfall[. §]_geld' in item:
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'Notfallgeld'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['[. §]', '_', '§']
                
                elif '[§ irgend]wohin' in item:
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'irgendwohin'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['[§ irgend]']

                # SPECIAL CASE:
                elif item == 'Wie_[s heißt]_der':  # Wie_[s heißt]_der --> make three tokens
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'Wie'
                    tok[current_tok_b_key] = 'heißt'
                    tok[current_tok_c_key] = 'der'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key]
                    anno[current_span_key] = ['_', '[s heißt]', '_']

                # SPECIAL CASE:
                elif item == 'rennt_er_[§ .]_Heute':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_d_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'rennt'
                    tok[current_tok_b_key] = 'er'
                    tok[current_tok_c_key] = '.'
                    tok[current_tok_d_key] = 'Heute'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key, current_tok_d_key]
                    anno[current_span_key] = ['_', '_', '[§ .]', '_']

                elif item == "er_war_[zuf*iden zufrieden]":
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'er'
                    tok[current_tok_b_key] = 'war'
                    tok[current_tok_c_key] = 'zufrieden'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key]
                    anno[current_span_key] = ['_', '_', '[zuf*iden zufrieden]']
                    continue

                elif item == "Geburtstags[§ geschenk]":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'Geburtstagsgeschenk'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[§ geschenk]']
                    continue

                elif item == "Kriminal§[Polizei polizist]":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'Kriminalpolizist'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['§', '[Polizei polizist]']
                    continue

                elif item == "km[§ /]h{F}":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'km/h'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[§ /]', '{F}']
                    continue

                elif item == "24[. :]00":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = '24:00'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[. :]']
                    continue

                elif item == "9[. :]30":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = '9:30'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[. :]']
                    continue

                elif item == "b[. §]z[. §]w":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'bzw'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[. §]', '[. §]']
                    continue

                elif item == "u[. §]s[. §]w":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'usw'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[. §]', '[. §]']
                    continue

                elif item == "us[. §]w":
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = 'usw'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['[. §]']
                    continue

                elif '_[' in item and '§]' in item:
                    item_normalized = item.split('_[')[0]

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item_normalized
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['_', item.split('_')[1]]

                elif '_[' in item:  # Und_[an dann] --> make two tokens; [i in]_[em den] --> make two tokens

                    item_a = item.split('_')[0]
                    item_b = item.split('_')[1]

                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)

                    if ' ' in item_a:  # handle cases like this: [i in]_[em den]
                        item_a_norm = item_a.split()[1]  # [i in] --> in] --> in
                        item_a_normalized = item_a_norm[:len(item_a_norm) - 1]
                        item_b_norm = item_b.split()[1]  # [em den] --> den] --> den
                        item_b_normalized = item_b_norm[:len(item_b_norm) - 1]
                    else:  # handle cases like this: Und_[an dann]
                        item_a_normalized = item_a
                        item_b_norm = item_b.split()[1]  # [an dann] --> dann] --> dann
                        item_b_normalized = item_b_norm[:len(item_b_norm) - 1]

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                    if ' ' in item_a:  # handle cases like this: [i in]_[em den]
                        anno[current_span_key] = [item_a, '_', item_b]
                    else:  # handle cases like this: Und_[an dann]
                        anno[current_span_key] = ['_', item_b]

                # [*eb lebt]_er{G} --> make two tokens
                # [zu nach]_Hause --> make two tokens
                # [s*b* zu]_finden --> make two tokens
                elif ']_' in item:
                    item_a = item.split('_')[0]
                    item_b = item.split('_')[1]

                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)

                    item_a_norm = item_a.split()[1]  # [*eb lebt] --> lebt] --> lebt
                    item_a_normalized = item_a_norm[:len(item_a_norm) - 1]

                    if '{' in item_b:  # er{G} --> er
                        annotation = re.findall('({.})', item_b)
                        anno_symbol = annotation[0]
                        item_b_normalized = re.sub(r'\{.\}', '', item_b)
                    else:
                        item_b_normalized = item_b

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                    if '{' in item_b:  # handle cases like this: [*eb lebt]_er{G}
                        anno[current_span_key] = [item_a, '_', anno_symbol]
                    else:  # handle cases like this: [s*b* zu]_finden
                        anno[current_span_key] = [item_a, '_']

                # alt_aus[§ sahen] --> make two tokens
                elif '_' in item and '[§' in item:
                    item_a = item.split('_')[0]
                    item_b = item.split('_')[1]

                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)

                    item_a_normalized = item_a
                    item_b_norm = re.sub(r'\[§ ', '', item_b)
                    item_b_normalized = re.sub(r'\]', '', item_b_norm)

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]
                    anno[current_span_key] = ['_', '[§ ' + item_b.split()[1]]

                # rein§[§ kommt] --> make 1 token
                elif '§[§' in item:
                    current_tok_key = "tok" + str(count + count_tok_insertions)

                    item_norm = re.sub(r'§\[§ ', '', item)
                    item_normalized = re.sub(r'\]', '', item_norm)

                    tok[current_tok_key] = item_normalized
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_key]
                    anno[current_span_key] = ['§', '[' + item.split('[')[1]]

    return tok, span, anno

"""
    USED TO CREATE THE EXPANDED TEXT OF THE 'ACHIEVED' LAYER
    Creates tok dict (expanded achieved strings), span dict, annotation dict by resolving error annotation symbols
    
    Example
        Input list: [Er, war, klücklich, und{2}, war, in_der, … si§ch, ,]
        Output dicts: -tok dict {tok1:Er, tok2:war, tok3:klücklich, tok4:und, tok5:und, tok6:inder, tok7:si, tok8:ch}
                      -span dict {span1:tok1, span2:tok2, span3:tok3, span4:[tok4,tok5], span5: tok6, span6:[tok7,tok8]}
                      -error dict {span4:{2}, span5:_, span6:§}
                      
    :arg token_list: a list of tokens
    :return: tok dict, span dict, error dict
"""
def create_tok_span_anno_achieved(token_list):

    tok = dict()
    span = dict()
    anno = dict()

    count_tok_insertions = 0  # always increase by 1 if a token is split into two tokens, e.g. in_der --> in der
    for count, item in enumerate(token_list):

        # first deal with all letter- and word-level annotations
        if "[" not in item:

            if item == '={N}':  # 2{N} *{N} 4{N} ={N}  the equals sign is supposed to be an arithmetic symbol
                item = '='

                current_tok_key = "tok" + str(count + count_tok_insertions)
                tok[current_tok_key] = item
                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key
                anno[current_span_key] = ['{N}']
                continue

            # handle all repeated words with {2}, {3}, {4}
            if '{2}' in item or '{3}' in item or '{4}' in item:

                # treat cases like  es_Wise--N{2}  warum_er{2}  er_get{2}
                if '_' in item and item.endswith('}'):
                    repetition_count = item[len(item) -2]
                    item_b = item.split('_')[1][:-3]
                    item_nonumber = item[:-3]
                    for x in range(int(repetition_count)-1):  # convert es_Wise--N{2} into: es_Wise--N Wise--N
                        item_nonumber = item_nonumber + ' ' + item_b

                    symbols = re.findall('(_)|(--)|(~)|(\{[A-Z]\})', item_nonumber)
                    symbol_list = []
                    symbol_list.append('{' + repetition_count + '}')
                    if len(symbols) > 0:
                        # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                        for i in symbols:
                            for j in i:
                                if len(j) > 0:
                                    symbol_list.append(j)

                    # convert es_Wise--N Wise--N into: esWiseN WiseN
                    item_nounderscore = re.sub(r'_', '', item_nonumber)
                    item_nodoubledash = re.sub(r'--', '', item_nounderscore)
                    item_notilde = re.sub(r'~', '-', item_nodoubledash)
                    normalized_item = re.sub(r'\{[A-Z]\}', '', item_notilde)

                    tokens = normalized_item.split()
                    tok_key_list = []
                    for t in tokens:
                        current_tok_key = "tok" + str(count + count_tok_insertions)
                        tok_key_list.append(current_tok_key)
                        count_tok_insertions = count_tok_insertions + 1
                        tok[current_tok_key] = t

                    count_tok_insertions = count_tok_insertions - 1
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = tok_key_list
                    anno[current_span_key] = symbol_list
                    continue

                # treat cases like kam{2}_nicht
                elif '_' in item and not item.endswith('}'):
                    item_a = item.split('_')[0]
                    repetition_count = item[len(item_a) - 2]
                    item_a_nonumber = item_a[:-3]
                    full_item_nonumber = re.sub(r'\{[0-9]\}', '', item)

                    item_expanded = ""
                    for x in range(int(repetition_count)-1):  # convert kam{2}_nicht into: kam kam_nicht
                        item_expanded += ' ' + full_item_nonumber

                    symbols = re.findall('(_)|(--)|(~)|(\{[A-Z]\})', full_item_nonumber)
                    symbol_list = []
                    symbol_list.append('{' + repetition_count + '}')
                    if len(symbols) > 0:
                        # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                        for i in symbols:
                            for j in i:
                                if len(j) > 0:
                                    symbol_list.append(j)

                    # convert es_Wise--N Wise--N into: esWiseN WiseN
                    item_nounderscore = re.sub(r'_', '', full_item_nonumber)
                    item_nodoubledash = re.sub(r'--', '', item_nounderscore)
                    item_notilde = re.sub(r'~', '-', item_nodoubledash)
                    normalized_item = re.sub(r'\{[A-Z]\}', '', item_notilde)

                    tokens = normalized_item.split()
                    tok_key_list = []
                    for t in tokens:
                        current_tok_key = "tok" + str(count + count_tok_insertions)
                        tok_key_list.append(current_tok_key)
                        count_tok_insertions = count_tok_insertions + 1
                        tok[current_tok_key] = t

                    count_tok_insertions = count_tok_insertions - 1
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = tok_key_list
                    anno[current_span_key] = symbol_list
                    continue

                else:
                    # take care of cases like ha{4}  lieste{G}{3}  Kalinka{N}{3}  den{G}{2}... (number is in the end)
                    if '2' in item[-2:] or '3' in item[-2:] or '4' in item[-2:]:
                        repetition_count = item[len(item) - 2]
                        item_nonumber = item[:-3]

                    else:  # take care of cases like Schnüfeln{2}{G}  or  Pichu{2}{N}  (number is in the middle)
                        repetition_count = item[-5:-4]
                        word = item[:-6]
                        sym = item[-3:]
                        item_nonumber = word + sym

                    item_expanded = ""
                    for x in range(int(repetition_count)):  # convert kam{2}_nicht into: kam kam_nicht
                        item_expanded += ' ' + item_nonumber

                    symbols = re.findall('(_)|(--)|(~)|(\{[A-Z]\})', item_expanded)
                    symbol_list = []
                    symbol_list.append('{' + repetition_count + '}')
                    if len(symbols) > 0:
                        # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                        for i in symbols:
                            for j in i:
                                if len(j) > 0:
                                    symbol_list.append(j)

                    item_nounderscore = re.sub(r'_', '', item_expanded)
                    item_nodoubledash = re.sub(r'--', '', item_nounderscore)
                    item_notilde = re.sub(r'~', '-', item_nodoubledash)
                    normalized_item = re.sub(r'\{[A-Z]\}', '', item_notilde)

                    tokens = normalized_item.split()
                    tok_key_list = []
                    for t in tokens:
                        current_tok_key = "tok" + str(count + count_tok_insertions)
                        tok_key_list.append(current_tok_key)
                        count_tok_insertions = count_tok_insertions + 1
                        tok[current_tok_key] = t

                    count_tok_insertions = count_tok_insertions - 1
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = tok_key_list
                    anno[current_span_key] = symbol_list
                    continue

            # handle all symbols which are deleted or exchanged to get the normalized token: * -- _ ~ {N} {F} {G}
            # {F}, {G}, {N}  ---> delete
            # asterisk (*) ---> leave but put into annotation layer
            # a_b ---> merge these two words (in_der → inder)
            # a~b ---> replace tilde with hyphen
            # a--b ---> concatenate the two words (e.g. Hambur--ger => Hamburger)
            symbols = re.findall('(\*)|(_)|(--)|(~)|(\{[A-Z]\})', item)
            symbol_list = []
            if len(symbols) > 0:
                symbol_list = []  # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                for i in symbols:
                    for j in i:
                        if len(j) > 0:
                            symbol_list.append(j)

                item_nounderscore = re.sub(r'_', '', item)
                item_nodoubledash = re.sub(r'--', '', item_nounderscore)
                item_notilde = re.sub(r'~', '-', item_nodoubledash)
                item = re.sub(r'\{[A-Z]\}', '', item_notilde)

                if '§' not in item and '=' not in item:
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = symbol_list

            if '§' in item and '=' in item or item.count("§") > 1 or item.count("=") > 1:

                if item == 'Free§fall=tower':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'Free'
                    tok[current_tok_b_key] = 'fall'
                    tok[current_tok_c_key] = 'tower'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['§', '='])
                    else:
                        anno[current_span_key] = ['§', '=']

                elif item == 'Rhein=Neckar=löwen':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'Rhein'
                    tok[current_tok_b_key] = 'Neckarlöwen'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['=', '='])
                    else:
                        anno[current_span_key] = ['=', '=']

                elif item == 'ABFOJA=Aller§Beste':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'ABFOJA=Aller'
                    tok[current_tok_b_key] = 'Beste'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['§'])
                    else:
                        anno[current_span_key] = ['§']

                elif item == 'Handball=Damen§Nationalmannschaft':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'Handball'
                    tok[current_tok_b_key] = 'Damen'
                    tok[current_tok_c_key] = 'Nationalmannschaft'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['=', '§'])
                    else:
                        anno[current_span_key] = ['=', '§']

                elif item == 'Java=chip=chocolate=cream':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_d_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'Java'
                    tok[current_tok_b_key] = 'chip'
                    tok[current_tok_c_key] = 'chocolate'
                    tok[current_tok_d_key] = 'cream'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key, current_tok_d_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['=', '=', '='])
                    else:
                        anno[current_span_key] = ['=', '=', '=']

                elif item == 'ent§lang§zu§hangeln':
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_d_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = 'ent'
                    tok[current_tok_b_key] = 'lang'
                    tok[current_tok_c_key] = 'zu'
                    tok[current_tok_d_key] = 'hangeln'
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key, current_tok_d_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['§', '§', '§'])
                    else:
                        anno[current_span_key] = ['§', '§', '§']

                elif item in ['After=Show=Party', '5=sterne=hotel', 'Formel=1=fahrer', '5=gänge=menü', '1=Mann=wohnung',
                 'Rhein=Neckar=Löwen', '4=zimmer=wohnung', 'internet=unterwegs=Handys', 'gute=nacht=geschichtefor']:
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = item.split('=')[0]
                    tok[current_tok_b_key] = item.split('=')[1]
                    tok[current_tok_c_key] = item.split('=')[2]
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['=', '='])
                    else:
                        anno[current_span_key] = ['=', '=']

                elif item in ['U=bahn=systemen', 'Günter=gloz=anlage']:
                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = re.sub(r'=', '', item)
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['=', '='])
                    else:
                        anno[current_span_key] = ['=', '=']

                elif item.count('§') == 2 and not '=' in item:  # handle cases with 2 pgf symbols: 'a§b§c' or *eut§zu§tage
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_c_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = item.split('§')[0]
                    tok[current_tok_b_key] = item.split('§')[1]
                    tok[current_tok_c_key] = item.split('§')[2]
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key, current_tok_c_key]
                    if len(symbol_list) > 0:
                        anno[current_span_key] = symbol_list
                        anno[current_span_key].extend(['§', '§'])
                    else:
                        anno[current_span_key] = ['§', '§']
                else:
                    print("THIS EXCEPTIONAL CASE IS NOT YET HANDLED: ", item, ' and its symbol list: ', symbol_list)

            # a§b ---> write the two words apart
            elif '§' in item:
                current_tok_a_key = "tok" + str(count + count_tok_insertions)
                count_tok_insertions = count_tok_insertions + 1
                current_tok_b_key = "tok" + str(count + count_tok_insertions)

                item_a_normalized = item.split('§')[0]
                item_b_normalized = item.split('§')[1]

                tok[current_tok_a_key] = item_a_normalized
                tok[current_tok_b_key] = item_b_normalized

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                if len(symbol_list) > 0:
                    anno[current_span_key] = symbol_list
                    anno[current_span_key].append('§')
                else:
                    anno[current_span_key] = ['§']
                continue

            elif '=' in item:
                # first handle all the special cases
                if item == '=surfer':
                    item = 'surfer'

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key

                    anno[current_span_key] = symbol_list
                    anno[current_span_key].append('=')
                    continue

                elif item == 'Angel=':
                    item = 'Angel'

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['=']
                    continue

                elif item == 'Nord=':
                    item = 'Nord'

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['=']
                    continue

                elif item == 'ABOJA=':
                    item = 'ABOJA'

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['=']
                    continue

                elif item == 'drei=':
                    item = 'drei'

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['=']
                    continue

                elif item == '=)':  # this is supposed to be a smiley
                    continue

                elif item == '=':
                    item = 'fehlendeswort: -'

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = ['=']
                    continue

                else:
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)

                    item_a_normalized = item.split('=')[0]
                    item_b_normalized = item.split('=')[1]

                    tok[current_tok_a_key] = item_a_normalized
                    tok[current_tok_b_key] = item_b_normalized

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]

                if len(symbol_list) > 0:
                    anno[current_span_key] = symbol_list
                    anno[current_span_key].append('=')
                else:
                    anno[current_span_key] = ['=']


            else:  # it's a normal token without any annotation symbol
                current_tok_key = "tok" + str(count + count_tok_insertions)
                tok[current_tok_key] = item

                current_span_key = "sSpan" + str(count)
                span[current_span_key] = current_tok_key

        # then deal with all sentence-level annotations (items that do contain "[")
        else:
            # [§ fehlendeswort] ---> replace with fehlendeswort:unbekannt,
            # e.g.: Man kann sogar nicht nur von Land zu Land sondern auch von Planet zu Planet [§ fehlendeswort]
            # [§ b] ---> replace with fehlendeswort:bekannt
            # es wird schwebende Autos geben [§ und] Roboter
            # [a §] ---> replace annotation and brackets with a
            # mit Will{N} Smith{N} [in §] einen Tag verbringen
            # [a b] ---> take out the first word (a)
            # Weil ich [wi--*en wissen] wollte

            # first, handle simple cases like listed above (token with single []-bracket and first and last char are [ / ]
            if item.count("[") == 1 and item[0] == '[' and item[-1] == ']':

                first = item.split()[0]
                second = item.split()[1]

                current_tok_key = "tok" + str(count + count_tok_insertions)

                if '§' in first or 'fehlendeswort' in second:
                    if 'fehlendeswort' in second:  # [§ fehlendeswort] ---> replace with fehlendeswort:unbekannt
                        tok[current_tok_key] = 'fehlendeswort:unbekannt'
                    else:  # [§ b] ---> replace with fehlendeswort:bekannt
                        tok[current_tok_key] = 'fehlendeswort: ' + second[:-1]

                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = [item]  # add full item, e.g [§ fehlendeswort]

                elif '{2}' in item:  # [er{2} §] [hat{2} §] [si{2} §] [ist{2} §]
                    item_normalized = item.split()[0][1:-3] # convert [er{2} §] into: er
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = item_normalized
                    tok[current_tok_b_key] = item_normalized
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]
                    anno[current_span_key] = [item]

                else:  # [in §] or [wi--*en wissen] --> take first word as token (might be necessary to normalize)
                    first_item = first[1:]  # cut off '['

                    symbols = re.findall('(_)|(--)|(~)|(\{.\})', first_item)
                    symbol_list = []
                    symbol_list.append(item)  # add full item [wi--*en wissen] and then also possible other annotations
                    if len(symbols) > 0:
                        # turn [('', '', '', '', '{F}'), ('', '', '', '', '{F}')] into ['{F}', '{F}']
                        for i in symbols:
                            for j in i:
                                if len(j) > 0:
                                    symbol_list.append(j)

                    item_nounderscore = re.sub(r'_', '', first_item)
                    item_nodoubledash = re.sub(r'--', '', item_nounderscore)
                    item_notilde = re.sub(r'~', '-', item_nodoubledash)
                    normalized_item = re.sub(r'\{.\}', '', item_notilde)

                    tok[current_tok_key] = normalized_item
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = symbol_list

            # then take care of complicated cases:
            else:
                if '§' not in item:
                    # handle cases like:  [i in]_[em den]  [*eb lebt]_s{G}   wie_[s heißt]_der
                    item_list = []
                    for i in item.split('_'):
                        if ' ' in i:
                            first = i.split()[0][1:]
                            item_list.append(first)
                        else:
                            item_list.append(i)
                    item_joined = ''.join(item_list)

                    item_nounderscore = re.sub(r'_', '', item_joined)
                    item_nodoubledash = re.sub(r'--', '', item_nounderscore)
                    item_notilde = re.sub(r'~', '-', item_nodoubledash)
                    item_normalized = re.sub(r'\{.\}', '', item_notilde)

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item_normalized
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = [item]

                elif '§[' in item:  # SPECIAL CASES: Rein§[§ kommt]  and   Criminal§[Polizei polizist]
                    if item == 'Rein§[§ kommt]':
                        item_a = 'Rein'
                        item_b = 'fehlendeswort:kommt'
                    elif item == 'Criminal§[Polizei polizist]':
                        item_a = 'Criminal'
                        item_b = 'Polizei'
                    current_tok_a_key = "tok" + str(count + count_tok_insertions)
                    count_tok_insertions = count_tok_insertions + 1
                    current_tok_b_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_a_key] = item_a
                    tok[current_tok_b_key] = item_b
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = [current_tok_a_key, current_tok_b_key]
                    anno[current_span_key] = [item]

                else:
                    # handle cases like:  ahlt_aus[§ sahen]   Tag_[machen §]   notval[. §]_Gelt   Rent_er_[§ .]_heute
                    if '[§' in item:  # replace [§ a] with fehlendeswort:a
                        item_tmp = re.sub(r'\[§.+\]', '', item)
                    # handle cases like:  Tag_[machen §]    notval[. §]_Gelt
                    else:
                        tmp = re.sub(r'\[', '', item)
                        item_tmp = re.sub(r' §\]', '', tmp)

                    item_normalized = re.sub(r'_', '', item_tmp)

                    current_tok_key = "tok" + str(count + count_tok_insertions)
                    tok[current_tok_key] = item_normalized
                    current_span_key = "sSpan" + str(count)
                    span[current_span_key] = current_tok_key
                    anno[current_span_key] = [item]

    return tok, span, anno

