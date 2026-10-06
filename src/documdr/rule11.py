# SPDX-License-Identifier: MIT
"""Non-binding record of a person's Rule 11 statement. Spec 001."""

from __future__ import annotations

from documdr.disclaimer import RULE11_NOTICE

LIMBS = frozenset({"diagnostic_therapeutic", "physiological_monitoring", "other"})
IMPACTS = frozenset(
    {
        "none",
        "serious_deterioration_or_surgery",
        "death_or_irreversible",
        "vital_immediate_danger",
    }
)
STATED_CLASSES = frozenset({"I", "IIa", "IIb", "III"})

# The class in each sentence is the class the regulation text attaches to that
# combination. It is stored so a reviewer can see a mismatch. It is not applied.
_SENTENCES: dict[tuple[str, str], tuple[str, str]] = {
    ("diagnostic_therapeutic", "none"): (
        "IIa",
        "Rule 11: software intended to provide information used to take decisions "
        "with diagnosis or therapeutic purposes is Class IIa, except where a more "
        "serious impact stated in the rule applies.",
    ),
    ("diagnostic_therapeutic", "serious_deterioration_or_surgery"): (
        "IIb",
        "Rule 11: those diagnostic or therapeutic decisions are Class IIb where "
        "their impact may cause a serious deterioration of a person's state of "
        "health or a surgical intervention.",
    ),
    ("diagnostic_therapeutic", "death_or_irreversible"): (
        "III",
        "Rule 11: those diagnostic or therapeutic decisions are Class III where "
        "their impact may cause death or an irreversible deterioration of a "
        "person's state of health.",
    ),
    ("physiological_monitoring", "none"): (
        "IIa",
        "Rule 11: software intended to monitor physiological processes is Class IIa, "
        "except vital-parameter monitoring that could result in immediate danger.",
    ),
    ("physiological_monitoring", "vital_immediate_danger"): (
        "IIb",
        "Rule 11: monitoring of vital physiological parameters is Class IIb where "
        "the nature of variations could result in immediate danger to the patient.",
    ),
    ("other", "none"): (
        "I",
        "Rule 11: all other software is Class I.",
    ),
}

_STRICTEST_NOTE = (
    "Annex VIII rule 3.5: if several rules apply, the strictest rule and sub-rule "
    "apply. This record does not choose the strictest class."
)


def assess_rule11(
    *,
    limb: str,
    impact: str,
    stated_class: str,
    also_considered_rules: list[str] | None = None,
) -> dict:
    """Record what a person stated. Never replace stated_class."""
    if limb not in LIMBS:
        raise ValueError(f"unknown Rule 11 limb: {limb}")
    if impact not in IMPACTS:
        raise ValueError(f"unknown Rule 11 impact: {impact}")
    if stated_class not in STATED_CLASSES:
        raise ValueError(f"unknown stated class: {stated_class}")
    match = _SENTENCES.get((limb, impact))
    if match is None:
        text_class = None
        sentence = "No single Rule 11 sentence matches this combination of limb and impact."
        differs = True
    else:
        text_class, sentence = match
        differs = text_class != stated_class
    rules = []
    for rule in also_considered_rules or []:
        cleaned = rule.strip()
        if cleaned and cleaned not in rules:
            rules.append(cleaned)
    record = {
        "binding": False,
        "notice": RULE11_NOTICE,
        "limb": limb,
        "impact": impact,
        "stated_class": stated_class,
        "sentence": sentence,
        "sentence_class": text_class,
        "differs_from_stated_class": differs,
        "also_considered_rules": rules,
        "strictest_rule_note": _STRICTEST_NOTE if len(rules) > 1 else None,
    }
    return record
