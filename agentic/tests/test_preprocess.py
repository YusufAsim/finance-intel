"""Normalisation of the incoming question."""

from app.graph.nodes.preprocess import preprocess


def test_collapses_whitespace_and_lowercases():
    state = preprocess({"question": "  Son   ISLEMLERIMI goster  "})
    assert state["normalized"] == "son islemlerimi goster"


def test_keeps_the_original_question_trimmed():
    state = preprocess({"question": "  hello  "})
    assert state["question"] == "hello"


def test_folds_turkish_letters_to_ascii():
    state = preprocess({"question": "Geçen ay ne kadar harcadım"})
    assert state["normalized"] == "gecen ay ne kadar harcadim"


def test_folds_the_dotted_capital_i():
    state = preprocess({"question": "İŞLEMLER"})
    assert state["normalized"] == "islemler"


def test_missing_question_becomes_empty():
    assert preprocess({})["normalized"] == ""
