import os

def print_tree(startpath, indent=""):
    for item in sorted(os.listdir(startpath)):
        path = os.path.join(startpath, item)
        if os.path.isdir(path):
            print(f"{indent}├── {item}/")
            print_tree(path, indent + "│   ")
        else:
            print(f"{indent}├── {item}")

# Replace with the path to your Django project
project_path = "LR"
print_tree(project_path)
