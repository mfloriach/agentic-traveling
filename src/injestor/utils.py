import re


def scrub_pii(text: str) -> tuple[str, bool]:
    detected = False

    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL]",
        text,
    )
    if "[EMAIL]" in text:
        detected = True

    text = re.sub(
        r"\b\d{3}-\d{2}-\d{4}\b",
        "[ID_NUMBER]",
        text,
    )
    if "[ID_NUMBER]" in text:
        detected = True

    return text, detected
