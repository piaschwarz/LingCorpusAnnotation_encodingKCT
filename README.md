# Encoding Language Learner Corpora
This repository hosts code and resources to encode the _Karlsruhe Children's Text_ corpus and the _H2, E2, ERK1 Children's Writing_ corpus into a computationally digestible format.

## Corpora
_Karlsruhe Children's Text_: https://catalog.ldc.upenn.edu/LDC2015T22<br>
_H2, E2, ERK1 Children's Writing_: https://catalog.ldc.upenn.edu/LDC2018T05

## Encoding format
The chosen encoding format is [PAULA XML](http://www.sfb632.uni-potsdam.de/paula.html). This is a standoff XML format designed to represent a wide range of linguistically annotated textual and multi-modal corpora. PAULA allows to store each layer of annotation in a separate XML file which refer to the same raw data. This allows for easy upgrade and scalability.

## Requirements
Some of the scripts in this repository rely on external libraries: [`SpaCy`](https://spacy.io/), [`lxml`](https://lxml.de/index.html), [`img2pdf`](https://gitlab.mister-muffin.de/josch/img2pdf) and [`pyhunspell`](https://github.com/blatinier/pyhunspell), a set of Python bindings for the Hunspell spellchecker engine. Run the following commands to get them:

### lxml
```
pip install lxml
```
### SpaCy
```
pip install pip setuptools wheel
pip install spacy
python -m spacy download de_dep_news_trf
```
### img2pdf
```
pip install img2pdf
```
### pyhunspell
```
sudo apt-get install python3-dev
sudo apt-get install libhunspell-dev
pip install hunspell
```
