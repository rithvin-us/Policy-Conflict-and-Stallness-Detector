"""LLM Service for AI resolution suggestions."""

def suggest_resolution(conflict_data: dict) -> str:
    """Mock LLM resolution suggestion based on conflict type."""
    ctype = conflict_data.get("conflict_type")
    
    if ctype == "PRECEDENCE":
        return "AI Suggests: The lower level policy should be updated to explicitly state it is an exception to the corporate standard, or aligned to match."
    elif ctype == "DIRECT":
        return "AI Suggests: Merge the two policies into a single authoritative rule. The more restrictive requirement typically supersedes the lenient one."
    elif ctype == "TEMPORAL":
        return "AI Suggests: Ensure that both retention schedules do not apply to the same class of data. If they do, adopt the longer retention period."
    elif ctype == "PARAMETER":
        return "AI Suggests: Standardize the parameter across all systems or define boundary conditions where each parameter is valid."
    return "AI Suggests: Review the overlapping scopes and harmonize the language to remove ambiguity."
