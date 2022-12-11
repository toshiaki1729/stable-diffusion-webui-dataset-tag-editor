import launch
from modules.shared import cmd_opts

if 'all' in cmd_opts.use_cpu or 'interrogate' in cmd_opts.use_cpu:
    if not launch.is_installed("onnxruntime"):
        launch.run_pip("install onnxruntime", "requirements for using SmilingWolf/wd-v1-4-vit-tagger on CPU device")
else:
    if not launch.is_installed("onnxruntime-gpu"):
        launch.run_pip("install onnxruntime-gpu", "requirements for using SmilingWolf/wd-v1-4-vit-tagger on GPU device")