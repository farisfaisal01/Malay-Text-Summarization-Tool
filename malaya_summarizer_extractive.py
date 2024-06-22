import re

def split_into_sentences(text):
    """
    Splits the input text into sentences based on punctuation marks.

    Args:
    - text (str): The input text to be split into sentences.

    Returns:
    - list: A list of sentences.
    """
    sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
    sentences = sentence_endings.split(text)
    return sentences