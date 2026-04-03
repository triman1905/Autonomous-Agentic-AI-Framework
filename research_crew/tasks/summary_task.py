"""
summary_task.py
---------------
Task definition for the Research Synthesizer Agent.

Final stage of the pipeline:
Transforms structured evidence into a clean, citation-backed research report
with refinement explanation.
"""

from crewai import Task


def build_summary_task(synthesizer_agent, extraction_task: Task, topic: str) -> Task:
    """Create the Research Summary Task."""

    return Task(
        description=(
            f"You will receive a JSON array of evidence objects from the Extraction Agent.\n"
            f"The research topic is: '{topic}'\n\n"

            "HARD RULES — violating any of these is a critical failure:\n"
            "  1. ONLY use information present in the evidence array.\n"
            "  2. NEVER add facts not present in the evidence.\n"
            "  3. Every factual sentence in Key Insights must include citation [N].\n"
            "  4. If evidence for a section is absent, omit that section entirely.\n\n"

            "Produce the output in EXACT Markdown format below:\n\n"

            "# Final Report\n\n"
            "Write a concise 1–2 paragraph high-level summary of the research.\n"
            "Do NOT include citations in this section.\n\n"

            "# Research Summary\n\n"

            "## Key Insights\n"
            "Write 3–5 concise paragraphs summarising key findings.\n"
            "Do NOT use numbering, bullet points, or bold text.\n"
            "Each paragraph MUST include citation [N].\n\n"

            "## Methodology Overview (omit if no methodology evidence)\n"
            "Provide a concise explanation of methods, models, and datasets.\n\n"

            "## Benchmarks & Metrics (omit if no metrics evidence)\n"
            "| Metric | Value | Source |\n"
            "|--------|-------|--------|\n"
            "| ...    | ...   | [N]    |\n\n"

            "## Refinement & Iterative Improvement\n"
            "Describe how the research improved across iterations:\n\n"

            "Iteration 1 (Initial):\n"
            "- Explain limitations such as missing depth, weak structure, or lack of citations.\n\n"

            "Iteration 2 (Correction):\n"
            "- Explain improvements such as better structure, added citations, clearer insights.\n\n"

            "Iteration 3 (Refinement):\n"
            "- Explain final improvements such as completeness, benchmark inclusion, and clarity.\n\n"

            "## Sources\n"
            "[1] Title\nURL\n\n"
            "[2] Title\nURL\n\n"

            "STRICT FORMATTING RULES:\n"
            "  • No '---' separators\n"
            "  • No extra text before or after the report\n"
            "  • Output must start with '# Final Report'\n"
            "  • No bullet points or numbering in Key Insights\n"
            "  • URLs must match evidence exactly\n"
            "  • Do NOT hallucinate\n"
        ),

        expected_output=(
            "A complete Markdown research report including: Final Report summary, "
            "Key Insights (paragraph format with citations), optional Methodology Overview, "
            "optional Benchmarks & Metrics table, Refinement explanation across iterations, "
            "and a Sources list. No hallucinated content."
        ),

        agent=synthesizer_agent,
        context=[extraction_task],
    )