import os
from together import Together

together_client = Together(api_key=os.environ.get('TOGETHER_API_KEY', ''))