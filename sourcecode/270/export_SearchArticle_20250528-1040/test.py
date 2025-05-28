import os

def print_structure(root_path, prefix=""):
    for item in sorted(os.listdir(root_path)):
        full_path = os.path.join(root_path, item)
        if os.path.isdir(full_path):
            print(f"{prefix}📁 {item}/")
            print_structure(full_path, prefix + "    ")
        else:
            print(f"{prefix}📄 {item}")

if __name__ == "__main__":
    print("🔍 Projectstructuur:\n")
    root = os.getcwd()  # of geef handmatig mee: 'C:/pad/naar/project'
    print_structure(root)
