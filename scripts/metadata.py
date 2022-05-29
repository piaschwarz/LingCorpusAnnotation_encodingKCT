"""
Author: Pia Schwarz

This script contains the content for the overall corpus metadata
"""



name = "Karlsruhe Children's Text"
author = "Johanna Fay"
doi = "https://doi.org/10.35111/13mf-v667"
release_date = "October 15, 2015"
language = "German"
paper = "https://catalog.ldc.upenn.edu/docs/LDC2015T22/L1TLT_Data_Lavalley_Final.pdf"
description = "Karlsruhe Children's Text was developed by the Cooperative State University Baden-Württemberg, " \
    "University of Education and Karlsruhe Institute of Technology. It consists of over 14,000 freely " \
    "written, German sentences from more than 1,700 school children in grades one through eight. " \
    "The data collection was conducted in 2011-2013 at elementary and secondary schools in and around Karlsruhe, " \
    "Germany. Students were asked to write as verbose a text as possible. " \
    "Those in grades one to four were read two stories and were then asked to write their own stories. " \
    "Students in grades five through eight were instructed to write on a specific theme, " \
    "such as \"Imagine the world in 20 years. What has changed?\". " \
    "The goal of the collection was to use the data to develop a spelling error classification system. " \
    "Annotators converted the handwritten text into digital form with all errors committed by the writers; " \
    "they also created an orthographically correct version of every sentence. " \
    "Metadata about the text was gathered, including the circumstances under which it was collected, " \
    "information about the student writer and background about spelling lessons in the particular class. " \
    "In a second step, the students' spelling errors were annotated into general groupings: grapheme level, " \
    "syllable level, morphology and syntax. The files were anonymized in a third step. " \
    "This release also contains metadata regarding the writers’ language biography, teaching methodology, " \
    "age, gender and school year. The average age of the participants was 11 years, and the gender " \
    "distribution was nearly equal. Original handwriting is presented as JPEG format image files."

anno01 = "* represents an unreadable letter"
anno02 = "a_b a and b should have been written separately"
anno03 = "a§b a and b should have been joined"
anno04 = "a=b missing hyphen"
anno05 = "a~b wrongly placed hyphen"
anno06 = "a--b denotes split of word at end of line (not hyphen)"
anno07 = "a{n} n repetitions of word a"
anno08 = "a{F} foreign word defined by non-German graphemes foreign grapheme-phoneme correspondence"
anno09 = "a{G} grammatical errors not to be analyzed for spelling"
anno10 = "a{N} Names, not analysed with the spell tagger"
anno11 = "[§ fehlendeswort] an unknown deletion"
anno12 = "[§ b] a known deletion b"
anno13 = "[a §] an insertion a"
anno14 = "[a b] substitution of a for b: a is corrected on target side, e.g. Achieved: [seinne ihre], Target: [seine ihre]"
anno15 = "[a b_c] best guess of word boundary"
anno16 = "[a_b c] kanicht = ka[n nn n]icht"
anno17 = "[a *] some combinations of letters make up word a, the real word can not be identified"

def get_corpus_metadata():
    return dict(((k, eval(k)) for k in ['name', 'author', 'doi', 'release_date', 'language',
                                        'paper', 'description', 'anno01', 'anno02', 'anno03',
                                        'anno04', 'anno05', 'anno06', 'anno07', 'anno08', 'anno09',
                                        'anno10', 'anno11', 'anno12', 'anno13', 'anno14', 'anno15',
                                        'anno16', 'anno17']))
if __name__ == '__main__':
    print(get_corpus_metadata())
