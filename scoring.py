def score(characteristics, rules):
    score = rules['topic_rules'][characteristics.topic]
    priority = -score
    return priority