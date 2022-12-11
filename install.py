import launch

if not launch.is_installed("onnxruntime-gpu"):
    launch.run_pip("install onnxruntime-gpu", "requirements for using SmilingWolf/wd-v1-4-vit-tagger")