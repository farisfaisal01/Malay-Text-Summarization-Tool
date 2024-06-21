import os

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import logging

logging.basicConfig(level=logging.INFO)

from pprint import pprint
import warnings
warnings.filterwarnings('default')
import re

# minimum cleaning, just simply to remove newlines.
def cleaning(string):
    string = string.replace('\n', ' ')
    string = re.sub(r'[ ]+', ' ', string).strip()
    return string

