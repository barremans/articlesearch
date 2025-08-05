from . import nl, en

LABELS_BY_LANG = {
    "NL": nl.LABELS,
    "EN": en.LABELS,
}

def get_labels(language="NL"):
    return LABELS_BY_LANG.get(language.upper(), nl.LABELS)
