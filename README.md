
A GTK settings manager for HyDE Project's Hyprland Config. It just lists all the settings in a tabular for which makes it a bit easier and simpler to edit. initially, I made it to manage my own HyDE config (to make things faster obv)

![HyprControl Logo](icons/hyprcontrol.png)

Features:
        Lists all the Hyprland configuration files with a GTK interface
    
Dependencies
    Python
    PyGObject
    GTK 3

On Arch Linux/EndeavourOS(or other Arch based distros):

<pre>
sudo pacman -S python-gobject gtk3 python-pipx
pipx ensurepath </pre>

Or via pip (not recommended for GTK apps):

<pre>
pip install PyGObject</pre>

Installation
1. Clone the Repository

<pre>
git clone https://github.com/DriftFe/hyprcontrol.git
cd hyprcontrol</pre>

2. Install with pipx

This will:
    Install the app in an isolated environment
    Create the hyprcontrol command
    Automatically add the app to your application launcher and install the icon

<pre>
pipx install .</pre>
    
If you ever need to update, just pull the latest code and run pipx install . again.

Running the App

You can launch HyprControl from your application launcher/menu
or from the terminal:

<pre>
hyprcontrol</pre>

Application Launcher Integration

The installer will automatically:
    Create a .desktop entry in ~/.local/share/applications/
    Copy the app icon to ~/.local/share/icons/hicolor/scalable/apps/
    Update the icon cache

If you change the icon or .desktop file, just reinstall with pipx install . to update them.
Uninstallation

To remove the app and its launcher entry:

<pre>
pipx uninstall hyprcontrol
rm -f ~/.local/share/applications/hyprcontrol.desktop
rm -f ~/.local/share/icons/hicolor/scalable/apps/hyprcontrol.png
gtk-update-icon-cache ~/.local/share/icons/hicolor/</pre>

Developer Notes
    The installer uses a custom command in setup.py to automate .desktop and icon installation.
    Project structure:
    text
    hyprcontrol/
    ├── hyprcontroltk.py
    ├── setup.py
    ├── icons/
    │   └── hyprcontroltk.png
    └── README.md

If you want to package for other distros, see Python Packaging User Guide.

Troubleshooting
    App not in launcher?
    Try logging out and back in, or run:

    
    gtk-update-icon-cache ~/.local/share/icons/hicolor/

ModuleNotFoundError?
    Make sure your Python file is named hyprcontrol.py (underscores, not hyphens) and your setup.py uses py_modules=["hyprcontrol"].

Still stuck?
    Open an issue on the repo or ask in the Hyprland/Arch Linux community.

License

MIT

Enjoy!
