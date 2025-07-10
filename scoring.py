# scoring.py

def score(characteristics: dict, rules: dict, source_url: str) -> int:
    """
    Calculates a priority score for an article based on a set of rules
    and the article's extracted characteristics.

    Args:
        characteristics (dict): A dictionary containing the LLM-extracted
                                characteristics like 'topic', 'actionability',
                                and 'sentiment'.
        rules (dict): The dictionary of rules loaded from rules.json.
        source_url (str): The source RSS feed URL of the article.

    Returns:
        int: The calculated total priority score for the article.
    """
    total_score = 0

    # --- Rule 1: Score based on Topic ---
    # Safely get the topic from the characteristics dictionary.
    topic = characteristics.get('topic')
    if topic:
        # Safely get the score for this topic from the rules, defaulting to 0.
        topic_score = rules.get("topic_rules", {}).get(topic, 0)
        total_score += topic_score

    # --- Rule 2: Score based on Actionability ---
    actionability = characteristics.get('actionability')
    if actionability:
        actionability_score = rules.get("actionability_rules", {}).get(actionability, 0)
        total_score += actionability_score

    # --- Rule 3: Score based on Sentiment ---
    sentiment = characteristics.get('sentiment')
    if sentiment:
        sentiment_score = rules.get("sentiment_rules", {}).get(sentiment, 0)
        total_score += sentiment_score
        
    # --- Rule 4: Score based on Source URL ---
    # This rule doesn't depend on the LLM characteristics.
    source_score = rules.get("source_rules", {}).get(source_url, 0)
    total_score += source_score

    return total_score
