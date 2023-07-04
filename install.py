import launch

if not launch.is_installed("qrcode"):
    launch.run_pip("install qrcode", "requirements for sd-webui-qrcode")