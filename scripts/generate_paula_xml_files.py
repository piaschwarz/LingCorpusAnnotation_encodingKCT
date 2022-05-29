"""A module to generate PAULA XML files.

This module collects a number of functions to build xml files required by the
PAULA XML encoding scheme (http://www.sfb632.uni-potsdam.de/paula.html).

Functions overview:
    * build_text_xml: generates an xml file storing the primary text data, a
        strech of untokenized plain text.

    * build_tok_xml: generates an xml file storing tokens. For each token the
        length and its starting index in the primary text data are provided.

    * build_mark_xml: generates markable files consisting of a number of
        <mark> nodes. These mark elements group together areas of the data
        into spans that share common properties or attributes.
        It generates files such as "error.kct.<file_id>.error_mark.xml" and
        "pos.kct.<file_id>.pos_mark.xml".

    * build_feat_error_xml: generates the "error.kct.<file_id>.annoFeat.xml" file,
        assigning a set of error annotation symbols to each span of tokens of the
        primary text data for the achieved layer.

    * build_feat_pos_xml: generates the "pos.kct.<file_id>.annoFeat.xml" file.
        The function relies on Spacy and uses the de_dep_news_trf German language model,
        which offer two options when it comes to the POS tagset:
        - Universal POS tagset: https://universaldependencies.org/u/pos/
        - TIGER POS tagset: https://www.ims.uni-stuttgart.de/forschung/ressourcen/korpora/tiger/

    * build_doc_anno_xml: generates an annoSet file grouping the set of annotations
        used in a given document (i.e. each terminal directory in a PAULA encoded corpus).

    * build_doc_multifeat_xml: generates a multiFeat file, collecting all the metadata
        for a given document into a list of <feat> nodes.

    * build_corpus_anno_xml: generates an annoSet file for the corpus itself.

    * build_corpus_multifeat_xml: generates a multiFeat file, collecting all the metadata
        for the corpus itself e.g. author, doi, date of release, language.

    * build_scan_mark_xml: generates a markable file to align all tokens of a given layer
        to a pdf file, storing the text scan of such layer.

    * build_feat_scan_xml: generates an annoFeat file referencing the pdf scan of a given
        file and assigning it an id e.g. #scan_1.

TO DO:
    * improve build_doc_anno_xml so that struct items are not hard-coded.
    * improve build_doc_multifeat_xml. Right now the order of the keys
        in meta_dict is assumed to guarantee a correct 1:1 match with the
        items in eng_keys (e.g. "alter":"age", "geschlecht":"gender").
    * check whether build_doc_multifeat_xml and build_corpus_multifeat_xml
        can be merged into a single function.
    * check whether build_doc_anno_xml and build_corpus_anno_xml can be merged
        into a single function.

Author: Matteo Brivio
"""



import spacy, re
from lxml import etree



def build_text_xml(toks, layer, file_id, path):
    """Creates an xml file encoding the primary text data for a specific
    layer (e.g. normalized, achieved).

    Parameters:
        toks: a dictionary of tokens to be concatenated.
        layer: the reference layer of the text (e.g. normalized).
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Return:
        an xml file encoding the primary text data for the given layer.
    """
    file_name = f"{layer.lower()}.kct.{file_id}.text"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name, "type":"text"})
    body = etree.SubElement(top, "body")

    text = " ".join([val for val in toks.values()])

    body.text = text

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, doctype="<!DOCTYPE paula SYSTEM \"paula_text.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_tok_xml(toks, layer, file_id, path):
    """Creates a tok.xml file storing a number of `<mark>` nodes e.g.
    `<mark id="sTok0" xlink:href="#xpointer(string-range(//body,'',1,2))"/>`.

    Each node has two attributes, an `id` corresponding to a token
    in the `toks` dictionary and an `xlink:href` specifying the start
    index and the length of the token.

    Parameters:
        toks: a dictionary storing word tokens e.g. `{tok0:lesen}`.
        layer: the reference layer of the tokens in toks (e.g. normalized).
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Return:
        a tok.xml file pertaining to the specified `layer`.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"{layer.lower()}.kct.{file_id}.tok"
    base_name = f"{layer.lower()}.kct.{file_id}.text.xml"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    mark_List = etree.SubElement(top, "markList", {"type": "tok",
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    start_ind = 1

    for key, val in toks.items():
        # create mark comment extracting the current token from toks
        mark_List.append(etree.Comment(toks[key].replace("-", "–")))

        # create mark node
        token_len = len(val)
        string_range = f"#xpointer(string-range(//body,'',{start_ind},{token_len}))"
        # compute the starting index of the next token
        start_ind += token_len + 1

        mark = etree.SubElement(mark_List, "mark", {"id": f"s{key.capitalize()}",
            etree.QName(xlink, "href"): string_range})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, doctype="<!DOCTYPE paula SYSTEM \"paula_mark.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_mark_xml(toks, layer, base, file_id, path, spans=None):
    """Creates a markable file storing a number of `<mark>` nodes.
    e.g. `<mark id="sSpan0" xlink:href="#sTok0"/>`.

    Each node has two attributes: an `id` corresponding to a key
    in the spans dictionary, and an `xlink:href` corresponding to
    to one or more keys in the toks dictionary. Thus, one span may
    reference more tokens.
    Mark elements identify and group areas of the data (one or more
    tokens) that share common properties or attributes, which are
    then specified in PAULA feat files.

    Args:
        spans: a dictionary storing `{span:token(s)}` pairs.
        toks: a dictionary storing word tokens e.g. `{tok0:lesen}`.
        layer: the layer of the current mark file e.g. error as in
        error.kct.0_0000.error_mark.
        base: the layer of the file to which this markable refers to
            e.g. achieved as in achieved.kct.0_0000.tok.xml.
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Returns:
        a markable file, specifying a number of spans.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"{layer.lower()}.kct.{file_id}.{layer.lower()}_mark"
    base_name = f"{base.lower()}.kct.{file_id}.tok.xml"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    mark_List = etree.SubElement(top, "markList", {"type": layer.lower(),
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    # if spans is None, create a 1 to 1 {span:tok} dictionary. This is the case
    # for pos_mark files, where each span corresponds to a single token.
    spans = spans or {f"sSpan{i}": tok for i, tok in enumerate(toks.keys())}

    for key, val in spans.items():
        is_list = isinstance(val, list)
        # create mark comment extracting token(s) from toks
        comment = toks[val] if not is_list else " ".join([toks[tok] for tok in val])
        mark_List.append(etree.Comment(comment.replace("-", "–")))

        # create mark node
        ref = f"#s{val.capitalize()}" if not is_list else " ".join([f"#s{tok.capitalize()}" for tok in val])
        mark = etree.SubElement(mark_List, "mark",
            {"id": key, etree.QName(xlink, "href"): ref})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, doctype="<!DOCTYPE paula SYSTEM \"paula_mark.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_feat_error_xml(spans, file_id, path):
    """Creates an annoFeat file storing a number of `<feat>` nodes.
    e.g. `<feat xlink:href="#sSpan0" value="~, {F}"/>`.

    Each node has two attributes, an `xlink:href` corresponding to a key
    in the spans dictionary and a value storing one or more error
    annotations (e.g. "§", "_", "{3}").
    Feat elements are applied to mark elements to annotate spans of one
    more tokens. For instance, given the tokens `und und`, identified by
    the mark item `<mark id="span0" xlink:href="#tok0 #tok1"/>`, the feat
    node `<feat xlink:href="#span0" value="{2}"/>` signifies that those
    two tokens share a common property i.e. they are a repetition error.

    Args:
        spans: a dictionary storing `{span:error_annotation(s)}` pairs.
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Returns:
        an annoFeat file with error annotations for each span of tokens in the
        achieved layer.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"error.kct.{file_id}.annoFeat"
    base_name = f"error.kct.{file_id}.error_mark.xml"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    feat_List = etree.SubElement(top, "featList", {"type": "error",
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    for key, val in spans.items():
        # create feat node
        is_list = isinstance(val, list)
        error_anno = val if not is_list else " ".join(anno for anno in val)
        feat = etree.SubElement(feat_List, "feat",
            {etree.QName(xlink, "href"): f"#{key}", "value": error_anno})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, doctype="<!DOCTYPE paula SYSTEM \"paula_feat.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_feat_pos_xml(toks, file_id, path, use_ud_pos=True):
    """Creates an annoFeat file storing a number of `<feat>` nodes.
    e.g. `<feat xlink:href="#sSpan0" value="PRON"/>`.

    Each node has two attributes, an `xlink:href` referencing a
    span and a corresponding POS tag value.
    The function allows to choose between the Universal POS tagset
    and the TIGER tagset.

    Args:
        toks: a dictionary storing word tokens e.g. `{tok0:lesen}`.
        file_id: name of the corpus file being processed e.g. 0_0000.
        use_ud_pos: boolean flag. If True, use the Universal POS tagset,
            otherwise the TIGER tagset.
        path: path to the paula document where the file should be stored.

    Returns:
        a feat file with a POS tag for each token in the normalized layer.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    # load German transformer pipeline
    nlp = spacy.load("de_dep_news_trf")

    # get UD/TIGER pos for each token in toks
    pos = lambda doc: doc[0].pos_ if use_ud_pos else doc[0].tag_
    pos_list = [pos(doc) for doc in nlp.pipe(toks.values(),
        disable=["attribute_ruler", "lemmatizer"], batch_size=100)]

    file_name = f"pos.kct.{file_id}.annoFeat"
    base_name = f"pos.kct.{file_id}.pos_mark.xml"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    feat_List = etree.SubElement(top, "featList", {"type": "pos",
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    for i, pos in enumerate(pos_list):
        # create feat comment with token for current pos
        feat_List.append(etree.Comment(toks[f"tok{i}"].replace("-", "–")))

        # create feat node <feat xlink:href="#sSpanN" value="POS"/>
        feat = etree.SubElement(feat_List, "feat",
            {etree.QName(xlink, "href"): f"#sSpan{i}", "value": pos})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, doctype="<!DOCTYPE paula SYSTEM \"paula_feat.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_doc_anno_xml(file_id, path):
    """Creates an annoSet file describing the set of annotations
    contained in the document (a terminal directory in a PAULA
    encoded corpus is a document). The file stores a number of
    `<struct>` nodes, each one collecting multiple `<rel>` nodes
    e.g. `<rel id="rel_1" xlink:href="achieved.0_0000.text.xml" />`.

    The annoSet file contains as many `rel` elements as there are
    xml files in the document, minus one, as the annoSet itself is
    not referenced.
    Different `structs` can group together files belonging to one
    logical annotation layer.

    Args:
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Returns:
        an annoSet file.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"kct.{file_id}.anno"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": "annoSet", "type": "STRUCT"})
    struct_List = etree.SubElement(top, "structList", {"type": "annoSet"},
        nsmap={"xlink": xlink})

    # create struct_1 (achieved) and its rel children
    struct_1 = etree.SubElement(struct_List, "struct", {"id": "anno_1"})
    etree.SubElement(struct_1, "rel", {"id": "rel_1",
        etree.QName(xlink, "href"): f"doc_{file_id}_achieved.text.xml"})
    etree.SubElement(struct_1, "rel", {"id": "rel_2",
        etree.QName(xlink, "href"): f"doc_{file_id}_achieved.tok.xml"})

    # create struct_2 (error) and its rel children
    struct_2 = etree.SubElement(struct_List, "struct", {"id": "anno_2"})
    etree.SubElement(struct_2, "rel", {"id": "rel_3",
        etree.QName(xlink, "href"): f"doc_{file_id}_error.mark.xml"})
    etree.SubElement(struct_2, "rel", {"id": "rel_4",
        etree.QName(xlink, "href"): f"doc_{file_id}_error.anno_feat.xml"})

    # create struct_3 (normalized) and its rel children
    struct_3 = etree.SubElement(struct_List, "struct", {"id": "anno_3"})
    etree.SubElement(struct_3, "rel", {"id": "rel_5",
        etree.QName(xlink, "href"): f"doc_{file_id}_normalized.text.xml"})
    etree.SubElement(struct_3, "rel", {"id": "rel_6",
        etree.QName(xlink, "href"): f"doc_{file_id}_normalized.tok.xml"})

    # create struct_4 (pos) and its rel children
    struct_4 = etree.SubElement(struct_List, "struct", {"id": "anno_4"})
    rel_7 = etree.SubElement(struct_4, "rel", {"id": "rel_7",
        etree.QName(xlink, "href"): f"doc_{file_id}_pos.mark.xml"})
    rel_8 = etree.SubElement(struct_4, "rel", {"id": "rel_8",
        etree.QName(xlink, "href"): f"doc_{file_id}_pos.anno_feat.xml"})

    # create struct_5 (scans) and its rel children
    struct_5 = etree.SubElement(struct_List, "struct", {"id": "anno_5"})
    etree.SubElement(struct_5, "rel", {"id": "rel_9",
        etree.QName(xlink, "href"): f"doc_{file_id}_pos.mark.xml"})
    etree.SubElement(struct_5, "rel", {"id": "rel_10",
        etree.QName(xlink, "href"): f"doc_{file_id}_pos.anno_feat.xml"})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, standalone=False,
        doctype="<!DOCTYPE paula SYSTEM \"paula_struct.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_doc_multifeat_xml(file_id, meta_dict, path):
    """Creates a multiFeat xml file, defining all the meta annotations
    for the current `file_id` PAULA document. The metaFeat file can stores
    one or more `<multiFeat>` nodes, each one collecting multiple `<feat>`
    items e.g. `<feat name="age" value="8"/>`.

    Args:
        file_id: name of the corpus file being processed e.g. 0_0000.
        meta_dict: a dictionary storing metadata for the current document.
        path: path to the paula document where the file should be stored.

    Returns:
        a multifeat file.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"kct.{file_id}.meta_multiFeat"
    base_name = f"kct.{file_id}.anno.xml"

    # English translations for keys in meta_dict
    eng_keys = ["child_age", "didactic_concept", "collection_year",
        "collection_month", "collection_day", "collecting_person",
        "child_gender", "child_name", "child_surname", "classroom",
        "grade", "L1", "replace_file", "elicitation_prompt", "school", "others",
        "transcriber", "transcriber_name"]

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    multi_feat_list = etree.SubElement(top, "multiFeatList", {"type": "multiFeat",
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    # metadata reference anno_1 (achieved layer) in the annoSet file
    multi_feat = etree.SubElement(multi_feat_list, "multiFeat",
        {etree.QName(xlink, "href"): "#anno_1"})

    for key, val in zip(eng_keys, meta_dict.values()):
        # create feat node
        feat = etree.SubElement(multi_feat, "feat",
            {"name": key, "value": val.replace("&#34;", "\'")})

    feat = etree.SubElement(multi_feat, "feat",
        {"name": f"scan", "value": f"{file_id}.pdf"})

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(etree.tostring(top, encoding="UTF-8",
            pretty_print=True, xml_declaration=True, standalone=False,
            doctype="<!DOCTYPE paula SYSTEM \"paula_multiFeat.dtd\">"))



def build_corpus_anno_xml(path):
    """Creates an annoSet file for the corpus itself. This is a
    prerequisite to have a `multiFeat` file storing metadata for
    the corpus level e.g. author, date of release, language.

    Args:
        path: path to the corpus directory collecting all Paula documents.

    Returns:
        an annoSet file.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"kct.anno"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name, "type": "STRUCT"})
    struct_List = etree.SubElement(top, "structList", {"type": "annoSet"},
        nsmap={"xlink": xlink})

    # create a single empty struct node
    struct_1 = etree.SubElement(struct_List, "struct", {"id": "anno_1"})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, standalone=False,
        doctype="<!DOCTYPE paula SYSTEM \"paula_struct.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_corpus_multifeat_xml(meta_dict, path):
    """Creates a multiFeat xml file, defining meta annotations for the
    corpus itself. The file stores one or more `<multiFeat>` items, which
    collect multiple `<feat>` nodes. Each node store a piece of metadata
    pertaining to the corpus e.g. `<feat name="author" value="Johanna Fay"/>`.

    Args:
        meta_dict: a dictionary storing the corpus metadata e.g. author,
            doi, date of release, language.
        path: path to the corpus directory collecting all Paula documents.

    Returns:
        a multifeat file storing corpus-level metadata.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"kct.meta_multiFeat"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    multi_feat_list = etree.SubElement(top, "multiFeatList", {"type": "multiFeat",
        etree.QName(xml, "base"): "kct.anno.xml"}, nsmap={"xlink": xlink})

    # meta data references anno_1 in corpus anno.xml
    multi_feat = etree.SubElement(multi_feat_list, "multiFeat",
        {etree.QName(xlink, "href"): "#anno_1"})

    for key, val in meta_dict.items():
        # create feat node
        feat = etree.SubElement(multi_feat, "feat", {"name": key, "value": val})

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(etree.tostring(top, encoding="UTF-8",
            pretty_print=True, xml_declaration=True, standalone=False,
            doctype="<!DOCTYPE paula SYSTEM \"paula_multiFeat.dtd\">"))



def build_scan_mark_xml(toks, base, file_id, path):
    """Creates a markable file storing a single `<mark>` node referencing the entire
    range of tokens in toks e.g.
    `<mark id="scan_1" xlink:href="#xpointer(id('sTok0')/range-to(id('sTok121')))"/>`.

    This allows to allign the layer represented by such tokens to a single pdf scan
    storing the originally elicited text for the given file_id.

    Args:
        toks: a dictionary storing word tokens e.g. `{tok0:lesen}`.
        base: layer to which the scan should refer to e.g. achieved.
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Returns:
        a markable file, aligning a range of tokens to a pdf scan.
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"scan.kct.{file_id}.pdf_mark"
    base_name = f"{base.lower()}.kct.{file_id}.tok.xml"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    mark_List = etree.SubElement(top, "markList", {"type": "scan_markable",
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    # create a mark node referencing the entire range of tokens in toks
    mark = etree.SubElement(mark_List, "mark", {"id": "scan_1",
    etree.QName(xlink, "href"): f"#xpointer(id('sTok0')/range-to(id('sTok{len(toks)-1}')))"})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, standalone=False,
        doctype="<!DOCTYPE paula SYSTEM \"paula_mark.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)



def build_feat_scan_xml(file_id, path):
    """Creates an annoFeat file storing a single `<feat>` node,
    referencing the pdf scan for the current file.

    Args:
        file_id: name of the corpus file being processed e.g. 0_0000.
        path: path to the paula document where the file should be stored.

    Retunrs:
        None
    """
    xlink = "http://www.w3.org/1999/xlink"
    xml = "http://www.w3.org/XML/1998/namespace"

    file_name = f"scan.kct.{file_id}.pdf_annoFeat"
    base_name = f"scan.kct.{file_id}.pdf_mark.xml"

    top = etree.Element("paula", {"version":"1.1"})
    header = etree.SubElement(top, "header", {"paula_id": file_name})
    feat_List = etree.SubElement(top, "featList", {"type": "pdf",
        etree.QName(xml, "base"): base_name}, nsmap={"xlink": xlink})

    # create feat node <feat xlink:href="#scan_1" value="0_0000.pdf"/>
    feat = etree.SubElement(feat_List, "feat",
        {etree.QName(xlink, "href"): f"#scan_1", "value": f"{file_id}.pdf"})

    serialized_XML = etree.tostring(top, encoding="UTF-8", pretty_print=True,
        xml_declaration=True, standalone=False,
        doctype="<!DOCTYPE paula SYSTEM \"paula_feat.dtd\">")

    with open(f"{path}/{file_name}.xml", "wb") as out_file:
        out_file.write(serialized_XML)
