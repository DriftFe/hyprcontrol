import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import os
import re

ACCENT = "#3584e4"

def expand_hyprland_vars(path, extra_env=None):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    unresolved = False

    def repl_env_var(match):
        var = match.group(1)
        value = os.environ.get(var)
        if value is None:
            nonlocal unresolved
            unresolved = True
            return match.group(0)
        return value
    path = re.sub(r'\$env\.([A-Za-z_][A-Za-z0-9_]*)', repl_env_var, path)

    if extra_env:
        for k, v in extra_env.items():
            if f"${k}" in path:
                if v is None:
                    unresolved = True
                path = path.replace(f"${k}", v if v is not None else f"${k}")

    if re.search(r'\$\{?[\w.]+\}?', path):
        unresolved = True

    return path, not unresolved

def read_config_file(path):
    try:
        with open(path, 'r') as f:
            return f.readlines()
    except FileNotFoundError:
        return []

def find_sources(lines, base_dir, extra_env=None):
    sources = []
    source_re = re.compile(r'^\s*source\s*=\s*(.+)')
    for line in lines:
        m = source_re.match(line)
        if m:
            src = m.group(1).strip()
            src = src.split('#', 1)[0].strip()
            if not src:
                continue
            expanded_src, resolved = expand_hyprland_vars(src, extra_env)
            if not resolved:
                continue
            if not os.path.isabs(expanded_src):
                expanded_src = os.path.normpath(os.path.join(base_dir, expanded_src))
            sources.append(expanded_src)
    return sources

def parse_settings(lines):
    settings = []
    setting_re = re.compile(r'^\s*([^#][^=\s]*)\s*=\s*(.+)$')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = setting_re.match(line)
        if m:
            key, value = m.group(1), m.group(2)
            settings.append((i, key, value))
    return settings

def update_lines_with_settings(lines, settings):
    for line_no, key, value in settings:
        lines[line_no] = f"{key} = {value}\n"
    return lines

def load_all_configs(main_config_path, extra_env=None):
    visited = set()
    configs = []

    def load_config(path):
        if path in visited:
            return
        visited.add(path)
        lines = read_config_file(path)
        configs.append((path, lines))
        base_dir = os.path.dirname(path)
        for src in find_sources(lines, base_dir, extra_env):
            load_config(src)

    load_config(main_config_path)
    return configs

class ConfigPage(Gtk.Box):
    def __init__(self, configs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        self.set_margin_top(18)
        self.set_margin_bottom(18)
        self.set_margin_start(18)
        self.set_margin_end(18)
        self.configs = configs
        self.current_file_index = 0

        # Sidebar: config files
        self.file_list = Gtk.ListBox()
        self.file_list.set_size_request(170, -1)
        for i, (path, _) in enumerate(self.configs):
            row = Gtk.ListBoxRow()
            row.set_name("sidebar_option")
            row.set_margin_top(3)
            row.set_margin_bottom(3)
            label = Gtk.Label(label=os.path.basename(path), xalign=0)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            label.set_margin_start(18)
            label.set_margin_end(18)
            row.add(label)
            self.file_list.add(row)
        self.file_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.file_list.connect("row-selected", self.on_file_selected)
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_min_content_height(200)
        sidebar_scroll.set_min_content_width(170)
        sidebar_scroll.set_margin_right(48)
        sidebar_scroll.set_margin_left(8)
        sidebar_scroll.set_name("sidebar_bg")
        sidebar_scroll.add(self.file_list)

        # --- Search bar ---
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search key or value...")
        search_btn = Gtk.Button(label="Search")
        search_btn.connect("clicked", self.on_search)
        self.search_entry.connect("activate", self.on_search)
        search_box.pack_start(self.search_entry, True, True, 0)
        search_box.pack_start(search_btn, False, False, 0)

        # Table: settings
        self.settings_store = Gtk.ListStore(str, str)
        self.settings_view = Gtk.TreeView(model=self.settings_store)
        renderer_key = Gtk.CellRendererText()
        renderer_key.set_property("editable", False)
        col_key = Gtk.TreeViewColumn("Key", renderer_key, text=0)
        self.settings_view.append_column(col_key)

        renderer_value = Gtk.CellRendererText()
        renderer_value.set_property("editable", True)
        renderer_value.connect("edited", self.on_value_edited)
        col_value = Gtk.TreeViewColumn("Value", renderer_value, text=1)
        self.settings_view.append_column(col_value)

        self.settings_view.set_headers_visible(True)
        self.settings_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.settings_view.set_hexpand(True)
        self.settings_view.set_vexpand(True)

        table_frame = Gtk.Frame()
        table_frame.set_shadow_type(Gtk.ShadowType.NONE)
        table_frame.set_name("card")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.settings_view)
        table_frame.add(scrolled)

        # Buttons
        self.save_button = Gtk.Button(label="Save")
        self.save_button.get_style_context().add_class("accent")
        self.save_button.set_margin_top(8)
        self.save_button.set_margin_bottom(8)
        self.save_button.connect("clicked", self.save_changes)
        self.reload_button = Gtk.Button(label="Reload Hyprland")
        self.reload_button.set_margin_top(8)
        self.reload_button.set_margin_bottom(8)
        self.reload_button.connect("clicked", self.reload_hyprland)
        btn_box = Gtk.Box(spacing=12)
        btn_box.pack_start(self.save_button, False, False, 0)
        btn_box.pack_start(self.reload_button, False, False, 0)

        # Layout
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_box.pack_start(Gtk.Label(label="Config Files", xalign=0), False, False, 0)
        left_box.pack_start(sidebar_scroll, True, True, 0)
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.info_label = Gtk.Label(label="Select a config file to view/edit settings.")
        self.info_label.set_xalign(0)
        right_box.pack_start(self.info_label, False, False, 0)
        right_box.pack_start(search_box, False, False, 0)
        right_box.pack_start(table_frame, True, True, 0)
        right_box.pack_start(btn_box, False, False, 0)
        self.pack_start(left_box, False, False, 0)
        self.pack_start(right_box, True, True, 0)

        if len(self.configs) > 0:
            self.file_list.select_row(self.file_list.get_row_at_index(0))

    def on_file_selected(self, listbox, row):
        if not row:
            return
        index = row.get_index()
        self.current_file_index = index
        path, lines = self.configs[index]
        self.info_label.set_text(f"Editing: {path}")
        self.current_settings = parse_settings(lines)
        self.original_lines = lines.copy()
        self.settings_store.clear()
        for _, key, value in self.current_settings:
            self.settings_store.append([key, value])

    def on_value_edited(self, widget, path, text):
        self.settings_store[path][1] = text

    def save_changes(self, btn):
        if self.current_file_index is None:
            return
        path, lines = self.configs[self.current_file_index]
        updated_settings = []
        for i, (line_no, key, value) in enumerate(self.current_settings):
            new_value = self.settings_store[i][1]
            updated_settings.append((line_no, key, new_value))
        updated_lines = update_lines_with_settings(self.original_lines, updated_settings)
        try:
            with open(path, "w") as f:
                f.writelines(updated_lines)
            self.info_label.set_text(f"Saved changes to: {path}")
        except Exception as e:
            self.info_label.set_text(f"Failed to save: {e}")

    def reload_hyprland(self, btn):
        result = os.system("hyprctl reload")
        if result == 0:
            self.info_label.set_text("Hyprland configuration reloaded successfully.")
        else:
            self.info_label.set_text("Failed to reload Hyprland configuration.")

    def on_search(self, widget, *args):
        search_text = self.search_entry.get_text().strip().lower()
        if not search_text:
            return
        found = False
        # Search both key and value columns
        for i, row in enumerate(self.settings_store):
            key = row[0].lower()
            value = row[1].lower()
            if search_text in key or search_text in value:
                selection = self.settings_view.get_selection()
                tree_iter = self.settings_store.get_iter(Gtk.TreePath(i))
                selection.select_iter(tree_iter)
                self.settings_view.scroll_to_cell(Gtk.TreePath(i))
                found = True
                break
        if not found:
            self.info_label.set_text(f"No match for: {search_text}")

class MainWindow(Gtk.Window):
    def __init__(self, configs):
        super().__init__(title="HyprControl - GNOME Style")
        self.set_default_size(1050, 700)
        self.set_border_width(0)
        header = Gtk.HeaderBar(title="HyprControl")
        header.set_show_close_button(True)
        self.set_titlebar(header)
        # Sidebar
        sidebar = Gtk.ListBox()
        sidebar.set_selection_mode(Gtk.SelectionMode.SINGLE)
        sidebar.set_property("margin", 0)
        def make_sidebar_row(label, iconname):
            row = Gtk.ListBoxRow()
            row.set_name("sidebar_option")
            row.set_margin_top(3)
            row.set_margin_bottom(3)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon = Gtk.Image.new_from_icon_name(iconname, Gtk.IconSize.LARGE_TOOLBAR)
            lbl = Gtk.Label(label=label, xalign=0)
            lbl.set_margin_top(10)
            lbl.set_margin_bottom(10)
            lbl.set_margin_start(18)
            lbl.set_margin_end(18)
            hbox.pack_start(icon, False, False, 0)
            hbox.pack_start(lbl, True, True, 0)
            row.add(hbox)
            return row
        row1 = make_sidebar_row("Configs", "preferences-system-symbolic")
        sidebar.add(row1)
        # Sidebar scrolling
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_min_content_width(190)
        sidebar_scroll.set_margin_right(48)
        sidebar_scroll.set_margin_left(8)
        sidebar_scroll.set_name("sidebar_bg")
        sidebar_scroll.add(sidebar)
        # CSS for cards and sidebar options and controls
        css = b"""
        #card {
            background: #232323;
            border-radius: 20px;
            border: 1px solid #292929;
            padding: 18px;
            margin: 12px;
        }
        .accent {
            background: #3584e4;
            color: #fff;
            border-radius: 10px;
            padding: 8px 24px;
            font-weight: bold;
        }
        #sidebar_option {
            border-radius: 16px;
            margin: 4px 0px 4px 0px;
        }
        #sidebar_bg {
            background: #202124;
        }
        GtkListBoxRow:selected, GtkListBoxRow:selected:hover {
            background-color: #3584e4;
            color: #fff;
            border-radius: 16px;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        # Stack for pages
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(350)
        stack.add_titled(ConfigPage(configs), "configs", "Configs")
        # Link sidebar to stack
        def on_row_selected(box, row):
            if row:
                stack.set_visible_child_name(["configs"][row.get_index()])
        sidebar.connect("row-selected", on_row_selected)
        sidebar.select_row(row1)
        # Layout
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.pack_start(sidebar_scroll, False, False, 0)
        box.pack_start(stack, True, True, 0)
        self.add(box)
        self.show_all()

def main():
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main_config = os.path.expanduser("~/.config/hypr/hyprland.conf")
    configs = load_all_configs(main_config)
    win = MainWindow(configs)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
