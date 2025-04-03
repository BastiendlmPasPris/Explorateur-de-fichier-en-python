import tkinter as tk
from tkinter import ttk, messagebox
import os
import datetime
import platform

class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Explorateur de fichiers")
        self.geometry("1000x600")
        self.file_data = {}

        # Configuration du thème moderne
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('Treeview', 
                             background="#2b2b2b", 
                             foreground="white", 
                             fieldbackground="#2b2b2b",
                             font=('Helvetica', 10))
        self.style.map('Treeview', background=[('selected', '#347083')])
        self.style.configure('TButton', font=('Helvetica', 10), padding=5)
        self.style.configure('TEntry', font=('Helvetica', 10))
        self.style.configure('TLabel', font=('Helvetica', 10), foreground="#333")

        # Panneau principal
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Arborescence des dossiers (à gauche)
        self.tree_frame = ttk.Frame(self.paned, width=300)
        self.tree = ttk.Treeview(self.tree_frame, show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.populate_root()
        
        # Panneau de droite (liste des fichiers et détails)
        self.right_frame = ttk.Frame(self.paned)

        # Barre d'outils : bouton retour, saisie de chemin, case pour fichiers cachés
        self.toolbar = ttk.Frame(self.right_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        self.back_button = ttk.Button(self.toolbar, text="Retour", command=self.go_back)
        self.back_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.path_entry = ttk.Entry(self.toolbar)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.path_entry.bind('<Return>', self.navigate_to_path)
        
        self.show_hidden = tk.BooleanVar(value=False)
        self.hidden_checkbox = ttk.Checkbutton(self.toolbar, 
                                               text="Afficher fichiers cachés", 
                                               variable=self.show_hidden, 
                                               command=self.update_file_list)
        self.hidden_checkbox.pack(side=tk.LEFT, padx=(5,0))
        
        # Liste des fichiers avec menu contextuel (clic droit)
        self.file_list = ttk.Treeview(self.right_frame, 
                                      columns=('size', 'type', 'modified'), 
                                      selectmode='browse')
        self.file_list.heading('#0', text='Nom', command=lambda: self.sort_column('name', False))
        self.file_list.heading('size', text='Taille', command=lambda: self.sort_column('size', False))
        self.file_list.heading('type', text='Type', command=lambda: self.sort_column('type', False))
        self.file_list.heading('modified', text='Modifié', command=lambda: self.sort_column('modified', False))
        self.file_list.column('#0', width=250)
        self.file_list.column('size', width=100)
        self.file_list.column('type', width=150)
        self.file_list.column('modified', width=150)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        self.file_list.bind('<Double-1>', self.on_file_double_click)
        self.file_list.bind('<<TreeviewSelect>>', self.on_file_select)
        self.file_list.bind('<Button-3>', self.show_context_menu)
        
        # Menu contextuel proposant plusieurs actions
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Renommer", command=self.inline_rename)
        self.context_menu.add_command(label="Déplacer", command=self.inline_move)
        self.context_menu.add_command(label="Créer un nouveau fichier", command=self.inline_create_file)
        self.context_menu.add_command(label="Supprimer", command=self.delete_selected_file)
        
        # Panneau de détails (informations sur le fichier sélectionné)
        self.details_frame = ttk.Frame(self.right_frame)
        self.details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.details_labels = {}
        details = [
            ('Chemin:', 'path'),
            ('Taille:', 'size'),
            ('Type:', 'type'),
            ('Créé le:', 'created'),
            ('Modifié le:', 'modified'),
        ]
        for i, (label_text, key) in enumerate(details):
            ttk.Label(self.details_frame, text=label_text).grid(row=i, column=0, sticky='e', padx=2, pady=2)
            value_label = ttk.Label(self.details_frame, text='')
            value_label.grid(row=i, column=1, sticky='w', padx=2, pady=2)
            self.details_labels[key] = value_label
        
        self.paned.add(self.tree_frame, weight=1)
        self.paned.add(self.right_frame, weight=3)
        
        # Chemin de départ
        self.current_path = os.path.expanduser('~')
        self.update_path_entry()
        self.update_file_list()
        
        # Événements pour l'arborescence
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_open)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def populate_root(self):
        if platform.system() == 'Windows':
            for drive in self.get_windows_drives():
                node = self.tree.insert('', 'end', text=drive, values=[drive], tags=('directory',))
                self.tree.insert(node, 'end', text='dummy')
        else:
            root = '/'
            node = self.tree.insert('', 'end', text=root, values=[root], tags=('directory',))
            self.tree.insert(node, 'end', text='dummy')

    def get_windows_drives(self):
        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f'{letter}:\\'
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def on_tree_open(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)
        if children and self.tree.item(children[0], 'text') == 'dummy':
            self.tree.delete(children[0])
            path = self.tree.item(node, 'values')[0]
            self.populate_tree_node(node, path)

    def populate_tree_node(self, node, path):
        try:
            for entry in os.listdir(path):
                # Filtrer les fichiers cachés
                if not self.show_hidden.get() and entry.startswith('.'):
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    child = self.tree.insert(node, 'end', text=entry, values=[full_path], tags=('directory',))
                    self.tree.insert(child, 'end', text='dummy')
        except PermissionError:
            pass

    def on_tree_select(self, event):
        node = self.tree.focus()
        path = self.tree.item(node, 'values')[0]
        self.current_path = path
        self.update_path_entry()
        self.update_file_list()

    def update_path_entry(self):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.current_path)

    def update_file_list(self):
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        self.file_data = {}
        try:
            entries = os.listdir(self.current_path)
        except Exception:
            return
        
        dirs = []
        files = []
        for entry in entries:
            if not self.show_hidden.get() and entry.startswith('.'):
                continue
            full_path = os.path.join(self.current_path, entry)
            try:
                is_dir = os.path.isdir(full_path)
                stat_info = os.stat(full_path)
                if is_dir:
                    dirs.append((entry, full_path, stat_info))
                else:
                    files.append((entry, full_path, stat_info))
            except Exception:
                continue
        
        for group in [dirs, files]:
            group.sort(key=lambda x: x[0].lower())
            for entry, full_path, stat_info in group:
                is_dir = os.path.isdir(full_path)
                size = stat_info.st_size if not is_dir else 0
                mtime = stat_info.st_mtime
                size_str = self.format_size(size)
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M:%S')
                type_str = 'Dossier' if is_dir else f"{os.path.splitext(entry)[1]} Fichier"
                item_id = self.file_list.insert('', 'end', text=entry, 
                                              values=(size_str, type_str, mtime_str),
                                              tags=('directory' if is_dir else 'file',))
                self.file_data[item_id] = {
                    'path': full_path,
                    'size': size,
                    'type': type_str,
                    'mtime': mtime,
                    'ctime': stat_info.st_ctime
                }

    def format_size(self, size):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        while size >= 1024 and index < len(units)-1:
            size /= 1024
            index += 1
        return f"{size:.2f} {units[index]}" if index > 0 else f"{size} B"

    def on_file_double_click(self, event):
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        entry = self.file_list.item(item, 'text')
        full_path = os.path.join(self.current_path, entry)
        if os.path.isdir(full_path):
            self.current_path = full_path
            self.update_path_entry()
            self.update_file_list()
        else:
            self.open_file(full_path)

    def sort_column(self, col, reverse):
        items = [(self.file_list.item(item, 'text'), item) for item in self.file_list.get_children('')]
        if col == 'name':
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        else:
            key_map = {'size': 'size', 'type': 'type', 'modified': 'mtime'}
            items.sort(key=lambda x: self.file_data[x[1]][key_map[col]], reverse=reverse)
        for index, (text, item) in enumerate(items):
            self.file_list.move(item, '', index)
        self.file_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    def on_file_select(self, event):
        item = self.file_list.selection()
        if item:
            item = item[0]
            data = self.file_data.get(item)
            if data:
                self.details_labels['path'].config(text=data['path'])
                self.details_labels['size'].config(text=self.format_size(data['size']))
                self.details_labels['type'].config(text=data['type'])
                self.details_labels['created'].config(text=datetime.datetime.fromtimestamp(data['ctime']).strftime('%d/%m/%Y %H:%M:%S'))
                self.details_labels['modified'].config(text=datetime.datetime.fromtimestamp(data['mtime']).strftime('%d/%m/%Y %H:%M:%S'))

    def navigate_to_path(self, event):
        path = self.path_entry.get()
        if os.path.exists(path):
            self.current_path = path
            self.update_file_list()
        else:
            messagebox.showerror("Erreur", "Chemin introuvable")

    def go_back(self):
        parent = os.path.dirname(self.current_path)
        if parent and os.path.exists(parent) and parent != self.current_path:
            self.current_path = parent
            self.update_path_entry()
            self.update_file_list()

    def show_context_menu(self, event):
        item = self.file_list.identify_row(event.y)
        if item:
            self.file_list.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def inline_rename(self):
        """Renommer directement le fichier en éditant le nom dans la liste."""
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        bbox = self.file_list.bbox(item, '#0')
        if not bbox:
            return
        x, y, width, height = bbox
        entry = ttk.Entry(self.file_list)
        entry.place(x=x, y=y, width=width, height=height)
        current_name = self.file_list.item(item, 'text')
        entry.insert(0, current_name)
        entry.focus_set()
        def on_rename(event=None):
            new_name = entry.get().strip()
            if new_name and new_name != current_name:
                full_old_path = os.path.join(self.current_path, current_name)
                full_new_path = os.path.join(self.current_path, new_name)
                try:
                    os.rename(full_old_path, full_new_path)
                    self.update_file_list()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de renommer : {e}")
            entry.destroy()
        entry.bind('<Return>', on_rename)
        entry.bind('<FocusOut>', lambda event: entry.destroy())

    def inline_move(self):
        """Déplacer directement le fichier en modifiant son chemin dans le panneau de détails."""
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        data = self.file_data.get(item)
        if not data:
            return
        label = self.details_labels['path']
        x = label.winfo_x()
        y = label.winfo_y()
        width = label.winfo_width() if label.winfo_width() > 100 else 200
        entry = ttk.Entry(self.details_frame)
        entry.place(x=x, y=y, width=width)
        entry.insert(0, data['path'])
        entry.focus_set()
        def on_move(event=None):
            new_path = entry.get().strip()
            if new_path and new_path != data['path']:
                try:
                    os.rename(data['path'], new_path)
                    self.current_path = os.path.dirname(new_path)
                    self.update_path_entry()
                    self.update_file_list()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de déplacer le fichier : {e}")
            entry.destroy()
        entry.bind('<Return>', on_move)
        entry.bind('<FocusOut>', lambda event: entry.destroy())

    def inline_create_file(self):
        """Créer un nouveau fichier directement en éditant son nom."""
        # Positionner l'éditeur en haut de la liste (ou à défaut, en haut à gauche)
        children = self.file_list.get_children()
        if children:
            bbox = self.file_list.bbox(children[0], '#0')
        else:
            bbox = (0, 0, 250, 20)
        x, y, width, height = bbox if bbox else (0, 0, 250, 20)
        editor = ttk.Entry(self.file_list)
        editor.place(x=x, y=0, width=width, height=height)
        default_name = "nouveau_fichier.txt"
        editor.insert(0, default_name)
        editor.focus_set()
        def on_create(event=None):
            filename = editor.get().strip()
            if filename:
                full_path = os.path.join(self.current_path, filename)
                try:
                    # Création d'un fichier vide (mode 'x' pour lever une exception si existe)
                    with open(full_path, 'x'):
                        pass
                    self.update_file_list()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de créer le fichier : {e}")
            editor.destroy()
        editor.bind('<Return>', on_create)
        editor.bind('<FocusOut>', lambda event: editor.destroy())

    def delete_selected_file(self):
        """Supprimer le fichier ou dossier sélectionné."""
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        filename = self.file_list.item(item, 'text')
        full_path = os.path.join(self.current_path, filename)
        if messagebox.askyesno("Supprimer", f"Voulez-vous vraiment supprimer '{filename}' ?"):
            try:
                if os.path.isdir(full_path):
                    os.rmdir(full_path)
                else:
                    os.remove(full_path)
                self.update_file_list()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer : {e}")

    def open_file(self, path):
        # Personnalisez l'action d'ouverture du fichier ici
        messagebox.showinfo("Ouvrir", f"Ouverture du fichier : {path}")

if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
