"""A script calling the modules required to encoded the KCT corpus.

Functions overview:
    * process_dir: given raw text and jpg data, encodes them into a single PAULA document.

    * add_corpus_metadata: generates the xml files required by the PAULA format to include
        corpus-level metadata e.g. author, DOI, annotation symbols.

Author: Pia Schwarz, Matteo Brivio
"""



import shutil, img2pdf
from pathlib import Path
from metadata import get_corpus_metadata
from hunspell_check import spell_check
from extract_raw_corpus_data import parse_kct_file, build_kct_text
from target import tokenize, create_tok_span_anno_achieved, create_tok_span_anno_target
from generate_paula_xml_files import build_doc_anno_xml, build_feat_error_xml, build_mark_xml, \
    build_feat_pos_xml, build_doc_multifeat_xml, build_text_xml, build_tok_xml, \
    build_corpus_multifeat_xml, build_corpus_anno_xml, build_scan_mark_xml, build_feat_scan_xml



def process_dir(current_dir, output_path, dtd_path=None, spell_check=False):
    """Builds a PAULA document from the KCT data (txt file and jpg scan)
    in the current directory.

    First, a dedicated directory, `dest`, for the new PAULA document is created.
    The dtd files required by the PAULA format are copied into `dest` from the
    specified `dtd_path`, if the path is not provided the files are assumed to
    be in a folder located into the script directory.
    A number of functions defined in the `target` and `extract_raw_corpus_data`
    modules are subsequently applied to the raw KCT text and jpg data to generate
    the xml files required for the PAULA encoding format.

    Args:
        current_dir: path to a KCT directory e.g. kct/data/t_all/0_0000
        dtd_path: path to the directory storing the dtd files. If None,
            the dtd folder is assumed to be in the script directory.
        output_path: path to the directory storing the new KCT_encoded corpus.
        spell_check: boolean flag to activate or deactivate the spellchecker.

    Return:
        None
    """
    # given current_dir, create a path to a PAULA document
    # e.g. KCT_encoded/kct_docs/0_0000
    Path(output_path, current_dir.stem).mkdir(exist_ok=True)
    dest = Path(output_path, current_dir.stem)

    # copy dtd files into current PAULA document directory
    dtd_path = dtd_path or "dtd_files"
    for dtd in Path(dtd_path).iterdir():
        shutil.copy(dtd, dest)

    # convert all jpg files in current_dir into a single pdf
    # and store it into the current PAULA document directory
    jpgs = sorted([f.as_posix() for f in current_dir.rglob("*.jpg")])
    with open(f"{dest}/{current_dir.name}.pdf","wb") as f:
        f.write(img2pdf.convert(jpgs))

    # path to the raw kct txt file in current_dir
    txt = Path(current_dir, f"{current_dir.name}.txt")

    # extract target, achieve and metadata from txt
    tar, ach, meta = parse_kct_file(txt)

    # create TARGET-layer-related files
    text_tar = build_kct_text(tar)
    tokens_tar = tokenize(text_tar)
    toks_tar, span_tar, anns_tar = create_tok_span_anno_target(tokens_tar)

    if spell_check:
        spell_check(toks_tar, "de_DE.dic", "de_DE.aff", silent=True)

    build_text_xml(toks_tar, "normalized", current_dir.stem, dest)
    build_tok_xml(toks_tar, "normalized", current_dir.stem, dest)
    build_mark_xml(toks_tar, "pos", "normalized", current_dir.stem, dest, spans=None)
    build_feat_pos_xml(toks_tar, current_dir.stem, dest)

    # create ACHIEVED-layer-related files
    text_ach = build_kct_text(ach)
    tokens_ach = tokenize(text_ach)
    toks_ach, span_ach, anns_ach = create_tok_span_anno_achieved(tokens_ach)
    build_text_xml(toks_ach, "achieved", current_dir.stem, dest)
    build_tok_xml(toks_ach, "achieved", current_dir.stem, dest)

    # create files to align pdf scans to the achieved layer
    build_scan_mark_xml(toks_ach, "achieved", current_dir.stem, dest)
    build_feat_scan_xml(current_dir.stem, dest)

    # create ERROR-layer-related files
    build_mark_xml(toks_ach, "error", "achieved", current_dir.stem, dest, spans=span_ach)
    build_feat_error_xml(anns_ach, current_dir.stem, dest)

    # create METADATA-related files
    build_doc_anno_xml(current_dir.stem, dest)
    build_doc_multifeat_xml(current_dir.stem, meta, dest)



def add_corpus_metadata(output_path, corpus_meta_dict, dtd_path=None):
    """Creates and adds to `output_path` all the files required for the
    corpus-level metadata.

    The dtd files required by the PAULA format are copied into `output_path`
    from the specified `dtd_path`, if the path is not provided the files are
    assumed to be in a folder located into the script directory.
    The `build_corpus_multifeat_xml` function relies on the `corpus_meta_dict`
    dictionary to generate the multifeat.xml file storing information about
    the corpus itself e.g. author, DOI, annotation symbols.

    Args:
        output_path: path to the directory storing the new KCT_encoded
            corpus.
        corpus_meta_dict: dictionary storing the corpus metadata.
        dtd_path: path to the directory storing the dtd files. If None,
            the dtd folder is assumed to be in the script directory.

    Return:
        None
    """
    build_corpus_anno_xml(output_path)
    build_corpus_multifeat_xml(corpus_meta_dict, output_path)

    # copy dtd files into output_path
    dtd_path = dtd_path or "dtd_files"
    for dtd in Path(dtd_path).iterdir():
        shutil.copy(dtd, output_path)



def main():
    # create output directory for PAULA encoded KCT
    Path(Path.cwd(), "KCT_encoded").mkdir(exist_ok=True)

    source_kct_path = Path("../../test1")
    output_path = Path("KCT_encoded")

    # generate corpus metadata e.g. author, language
    corpus_meta = get_corpus_metadata()

    # process each directory in the given KCT path
    for directory in source_kct_path.glob("*/"):
        print(f"processing directory {directory}")
        process_dir(directory, output_path, dtd_path=None, spell_check=False)

    add_corpus_metadata(output_path, corpus_meta, dtd_path=None)



if __name__ == "__main__":
    main()
