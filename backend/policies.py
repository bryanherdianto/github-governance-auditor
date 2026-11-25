from backend.models import ControlDefinition

DEFAULT_CONTROLS: list[ControlDefinition] = [
    ControlDefinition(
        id="documentation",
        name="Documentation",
        description="Does the repository contain a nonempty README file?",
        criteria="Check for README.md, README.rst, README.txt, or README with substantive non-whitespace content.",
    ),
    ControlDefinition(
        id="licensing",
        name="Licensing",
        description="Does the repository use an approved license (MIT or Apache 2.0)?",
        criteria="Verify SPDX license via GitHub repository metadata and/or LICENSE file; only MIT or Apache-2.0 pass.",
    ),
    ControlDefinition(
        id="model_documentation",
        name="Model Documentation",
        description="Does the repository contain a model card?",
        criteria="Check for a model card file (e.g., model-card.md, MODEL_CARD.md) or dedicated model card documentation.",
    ),
    ControlDefinition(
        id="ai_transparency",
        name="AI Transparency",
        description="Are the model's intended use and limitations adequately documented?",
        criteria="Inspect model card or README for explicit sections/details on intended use, out-of-scope uses, and limitations.",
    ),
    ControlDefinition(
        id="security",
        name="Security",
        description="Does the repository contain a security policy?",
        criteria="Check SECURITY.md in root, .github/SECURITY.md, docs/SECURITY.md, or org-level <owner>/.github security policy.",
    ),
]


def format_policies_for_prompt(controls: list[ControlDefinition]) -> str:
    # Render governance controls into a concise prompt block.
    return "\n".join(f"- {c.name}: {c.description} ({c.criteria})" for c in controls)
