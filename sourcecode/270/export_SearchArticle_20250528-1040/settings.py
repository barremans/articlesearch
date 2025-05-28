#settings.py
import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "environment": "live",
    "show_stock": "S",
    "detail_modal": True,
    "label_settings": {
        "LABEL_WIDTH": 85.0,
        "LABEL_HEIGHT": 25.0,
        "BARCODE_TOP": 5.0,
        "BARCODE_LEFT": 5.0,
        "BARCODE_WIDTH_SCALE": 0.45,
        "BARCODE_HEIGHT_SCALE": 0.15,
        
        "ART_TOP": 10.0,
        "ART_LEFT": 10.0,
        
        "DESCRIPTION_TOP": 20.0,
        "DESCRIPTION_LEFT": 5.0,
        "DESCRIPTION_WIDTH": 40.0,
        
        "DATE_TOP": 5.0,
        "DATE_LEFT": 40.0,
        
        "INBOUND_TOP": 25.0,
        "INBOUND_LEFT": 0.0,
        
        "SUPPLIER_TOP": 25.0,
        "SUPPLIER_LEFT": 35.0,
        
        "FONT_SIZE_ART": 6.0,
        "FONT_SIZE_DESCRIPTION": 6.0,
        "FONT_SIZE_SUPPLIER": 6.0,
        "FONT_SIZE_INBOUND": 6.0,
        "FONT_SIZE_DATE": 6.0
    }
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = {**DEFAULT_SETTINGS, **data}

            # Dieper mergen voor label_settings
            if "label_settings" in data:
                merged["label_settings"] = {
                    **DEFAULT_SETTINGS["label_settings"],
                    **data["label_settings"]
                }

            # Automatisch aanvullen van ontbrekende keys
            save_settings(merged)
            return merged
    except Exception:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


# Individuele toegangsmethoden
def load_environment():
    return load_settings().get("environment", DEFAULT_SETTINGS["environment"])


def save_environment(env: str):
    settings = load_settings()
    settings["environment"] = env
    save_settings(settings)


def load_show_stock():
    return load_settings().get("show_stock", DEFAULT_SETTINGS["show_stock"])


def save_show_stock(val: str):
    settings = load_settings()
    settings["show_stock"] = val
    save_settings(settings)


def load_detail_modal() -> bool:
    return load_settings().get("detail_modal", DEFAULT_SETTINGS["detail_modal"])


def save_detail_modal(val: bool):
    settings = load_settings()
    settings["detail_modal"] = val
    save_settings(settings)


def load_label_settings() -> dict:
    return load_settings().get("label_settings", DEFAULT_SETTINGS["label_settings"])


def save_label_settings(new_settings: dict):
    settings = load_settings()
    settings["label_settings"] = {
        **DEFAULT_SETTINGS["label_settings"],
        **new_settings
    }
    save_settings(settings)
