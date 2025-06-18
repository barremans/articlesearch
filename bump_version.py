# bump_version.py
import re
import sys

VERSION_FILE = "version.py"
VALID_PARTS = ("patch", "minor", "major")

def bump_version(version, part="patch"):
    major, minor, patch = map(int, version.split("."))
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = patch = 0
    return f"{major}.{minor}.{patch}"

def main():
    if len(sys.argv) < 2:
        print(f"❌ Geef op welk deel van de versie je wil verhogen: {', '.join(VALID_PARTS)}")
        print("Voorbeeld: python bump_version.py minor")
        sys.exit(1)

    part = sys.argv[1].lower()
    if part not in VALID_PARTS:
        print(f"❌ Ongeldige optie '{part}'. Kies uit: {', '.join(VALID_PARTS)}")
        sys.exit(1)

    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Bestand '{VERSION_FILE}' niet gevonden.")
        sys.exit(1)

    match = re.search(r'(__version__\s*=\s*")(\d+\.\d+\.\d+)(")', content)
    if not match:
        print("❌ Versieregel niet gevonden in version.py")
        sys.exit(1)

    old_version = match.group(2)
    new_version = bump_version(old_version, part=part)

    new_content = re.sub(
        r'(__version__\s*=\s*")(\d+\.\d+\.\d+)(")',
        lambda m: f'{m.group(1)}{new_version}{m.group(3)}',
        content
    )

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Versie verhoogd van {old_version} naar {new_version}")

if __name__ == "__main__":
    main()
