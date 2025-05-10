from setuptools import setup
from setuptools.command.install import install
import os
import shutil

APP_NAME = "HyprControl"
EXEC_CMD = "hyprcontrol"
ICON_NAME = "hyprcontrol"
CATEGORIES = "Settings;Utility;"
DESKTOP_FILE = os.path.expanduser("~/.local/share/applications/hyprcontrol.desktop")
ICON_SRC = os.path.join(os.path.dirname(__file__), "icons", "hyprcontrol.png")
ICON_DEST = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/hyprcontrol.png")

class CustomInstall(install):
    def run(self):
        # Standard install
        install.run(self)
        # .desktop file
        os.makedirs(os.path.dirname(DESKTOP_FILE), exist_ok=True)
        with open(DESKTOP_FILE, "w") as f:
            f.write(f"""[Desktop Entry]
Name={APP_NAME}
Comment=Modern GTK settings manager for Hyprland
Exec={EXEC_CMD}
Icon={ICON_NAME}
Terminal=false
Type=Application
Categories={CATEGORIES}
StartupNotify=true
""")
        print(f"Installed desktop entry: {DESKTOP_FILE}")
        # Icon
        if os.path.exists(ICON_SRC):
            os.makedirs(os.path.dirname(ICON_DEST), exist_ok=True)
            shutil.copy2(ICON_SRC, ICON_DEST)
            print(f"Installed icon: {ICON_DEST}")
        else:
            print("Icon not found, skipping icon installation.")
        # Update icon cache
        try:
            import subprocess
            subprocess.run(["gtk-update-icon-cache", os.path.dirname(os.path.dirname(ICON_DEST))], check=True)
            print("Updated icon cache.")
        except Exception as e:
            print(f"Could not update icon cache: {e}")

setup(
    name="hyprcontrol",
    version="1.0",
    py_modules=["hyprcontrol"],
    install_requires=["PyGObject"],
    entry_points={
        "gui_scripts": [
            "hyprcontrol = hyprcontrol:main"
        ]
    },
    cmdclass={
        "install": CustomInstall,
    },
    include_package_data=True,
    description="A GTK settings manager for Hyprland",
    author="Drift",
    license="MIT",
)
