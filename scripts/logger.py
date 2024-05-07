def write(content):
    print("[tag-editor] " + content)

def warn(content):
    write(f"[tag-editor:WARNING] {content}")

def error(content):
    write(f"[tag-editor:ERROR] {content}")