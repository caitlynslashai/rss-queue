# scoring.py
import json

def score(characteristics: dict, rules: dict, source_url: str, scoring_config: list) -> int:
    """
    Calculates a priority score for an article using a dynamic set of rules
    defined in a configuration.

    Args:
        characteristics (dict): A dictionary containing the LLM-extracted
                                characteristics like 'topic', 'actionability',
                                and 'sentiment'.
        rules (dict): The dictionary of all rule data loaded from rules.json.
        source_url (str): The source RSS feed URL of the article.
        scoring_config (list): A list of rule configurations that specifies
                               which rules to apply.

    Returns:
        int: The calculated total priority score for the article.
    """
    total_score = 0

    # Loop through each rule defined in the scoring configuration.
    for rule_config in scoring_config:
        rule_key = rule_config.get("rule_key")
        characteristic_key = rule_config.get("characteristic_key")

        # Get the specific set of rules (e.g., the 'topic_rules' dictionary).
        rule_set = rules.get(rule_key, {})

        # Determine the value to look up in the rule set.
        # This handles the special case for 'source_url', which is not in the
        # LLM's characteristics dictionary.
        if characteristic_key == "source_url":
            value_to_score = source_url
        else:
            value_to_score = characteristics.get(characteristic_key)
        
        # If we have a valid value, get its score from the rule set and add it.
        if value_to_score:
            points = rule_set.get(value_to_score, 0)
            total_score += points

    return total_score
