def build_prompt(content_type: str, intelligence, rag_snippets, policy):
    return f"""
    System:
    You are a campaign strategist specializing in affiliate marketing for networks like {intelligence['network']}.
    Create {content_type} copy based only on the intelligence and research provided.
    DO NOT use templates or generic responses.
    Cite all factual claims referencing research [n].
    Avoid phrases prohibited by the network rules.

    Intelligence summary:
    {intelligence['summary']}

    Research snippets:
    {rag_snippets}

    Policy restrictions:
    {policy['forbidden']}
    """