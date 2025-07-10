from openai import OpenAI
import json 
from pydantic import BaseModel, Field, create_model
from typing import Literal
from dotenv import load_dotenv
from os import getenv

# Load environment variables once when the module is imported.
load_dotenv()

# --- Dynamic Model and Prompt Creation ---

def create_dynamic_llm_handler():
    """
    Reads config files and dynamically creates the Pydantic model,
    system prompt, and the handler function. This makes the system
    extensible without changing the code.
    """
    # Load the main configuration and the rules data
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    with open('config/rules.json', 'r') as f:
        rules = json.load(f)

    scoring_rules_config = config.get("SCORING_RULES", [])
    
    # --- Dynamically build the Pydantic model fields ---
    pydantic_fields = {}
    prompt_parts = []
    
    # Loop through the scoring rules defined in config.json
    for i, rule_config in enumerate(scoring_rules_config):
        rule_key = rule_config.get("rule_key")
        char_key = rule_config.get("characteristic_key")

        # We only want the LLM to extract characteristics, not the source_url
        if char_key == "source_url":
            continue

        # Get the possible values for this characteristic from rules.json
        possible_values = list(rules.get(rule_key, {}).keys())
        
        if not possible_values:
            continue

        # Create a Literal type for the possible values
        ValueLiteral = Literal[*possible_values]
        
        # Create the Pydantic field for the model
        pydantic_fields[char_key] = (ValueLiteral, Field(description=f"The {char_key} of the article."))
        
        # Add a part to the system prompt for this characteristic
        prompt_parts.append(f"{i+1}. The {char_key}, which must be one of: {possible_values}.")

    # Use Pydantic's create_model to build the class dynamically
    DynamicCharacteristicsResponse = create_model(
        'DynamicCharacteristicsResponse',
        **pydantic_fields,
        __base__=BaseModel
    )

    # --- Dynamically build the system prompt ---
    system_prompt = "Analyze the user-provided text. Extract the following characteristics:\n" + "\n".join(prompt_parts)

    # --- Define the actual handler function using the dynamic components ---
    def _get_dynamic_characteristics_openai(text: str) -> BaseModel | None:
        """Gets article characteristics using a dynamically generated model and prompt."""
        openai_key = getenv("OPENAI_API_KEY")
        if not openai_key:
            print("ERROR: OPENAI_API_KEY not found in environment.")
            return None

        client = OpenAI(api_key=openai_key)
        
        try:
            # Use the dynamically created model and prompt
            parsed_response = client.beta.chat.completions.parse(
                model="gpt-4.1-nano",
                messages=[   
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_model=DynamicCharacteristicsResponse
            )   
            return parsed_response
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    return _get_dynamic_characteristics_openai


# --- Public Function ---
# Create the handler function when the module is first imported
_dynamic_handler = create_dynamic_llm_handler()

def get_characteristics(model: str, text: str) -> BaseModel | None:
    """
    Asks a specified model to extract characteristics from article text.

    This function acts as a dispatcher to the appropriate model-specific function.
    
    Args:
        model (str): The name of the model to use (e.g., "openai").
        text (str): The text of the article to analyze.

    Returns:
        BaseModel | None: A Pydantic object with the extracted
                          characteristics, or None if an error occurs.
    """
    if model == "openai":
        # Call the dynamically created handler
        return _dynamic_handler(text=text)
    else:
        return None
