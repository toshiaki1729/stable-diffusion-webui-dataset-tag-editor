import launch

if not launch.is_installed("onnxruntime-gpu"):
    launch.run_pip("install onnxruntime-gpu", "requirements for dataset-tag-editor [onnxruntime-gpu]")