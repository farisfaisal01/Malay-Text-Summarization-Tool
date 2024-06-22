import os

# Disable GPU for this script
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import logging
import warnings
import re

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

# Suppress all warnings
warnings.filterwarnings('default')

def cleaning(string):
    """
    Perform minimum cleaning on the input string by removing newlines and extra spaces.
    
    Args:
    - string (str): The input string to be cleaned.
    
    Returns:
    - str: The cleaned string.
    """
    string = string.replace('\n', ' ')
    string = re.sub(r'[ ]+', ' ', string).strip()
    return string