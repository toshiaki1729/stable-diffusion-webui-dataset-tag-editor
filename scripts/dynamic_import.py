def dynamic_import(path: str):
    import os
    from modules import scripts, script_loading
    path = os.path.abspath(os.path.join(scripts.basedir(), path))
    return script_loading.load_module(path)