from openai import OpenAI
import json 
from pydantic import BaseModel, Field
from typing import Literal, Annotated
from dotenv import load_dotenv
from os import getenv

load_dotenv()

with open('config/rules.json', 'r') as f:
    rules = json.load(f)
    topic_names = list(rules['topic_rules'].keys())
    TopicLiteral = Literal[*rules['topic_rules']]

# Define base format: in this case, a topic from the available list
class CharacteristicsResponse(BaseModel):
    topic: TopicLiteral = Field(description="The single most relevant topic for the article")


def get_characteristics(model, text):
    # Ask a specified model to give each characteristic with rules for specified article text
    if model == "openai":
        return _get_characteristics_openai(text=text)
    else:
        pass

def _get_characteristics_openai(text):
    # Logic to get the characteristics (currently only topic) when using OPENAI models
    openai_key = getenv("OPENAI_API_KEY")

    client = OpenAI(api_key = openai_key)
    
    try:
        completion = client.beta.chat.completions.parse(
            model = "gpt-4.1-nano",
            messages=[  
                {"role": "system", "content": f"Extract the topic from the provided text from the options, which are {topic_names}. When more than one topic would fit, pick the most specific one that applies."},
                {"role": "user", "content": text}
            ],
            response_format = CharacteristicsResponse
        )   

        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Return a default response or re-raise the exception
        return None
