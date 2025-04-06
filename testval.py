import tkinter as tk                          # Importation de la bibliothèque tkinter pour l'interface graphique
from tkinter import ttk, messagebox           # Importation de ttk pour les widgets thématiques et messagebox pour les boîtes de dialogue
import os                                     # Module pour interagir avec le système de fichiers
import datetime                               # Module pour gérer les dates et heures
import platform                               # Module pour identifier le système d'exploitation

# Définition de la classe FileExplorer qui hérite de tk.Tk pour créer la fenêtre principale
class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()                    # Initialisation de la classe parente tk.Tk
        self.title("Explorateur de fichiers")  # Titre de la fenêtre
        self.geometry("1000x600")              # Taille de la fenêtre
        self.file_data = {}                    # Dictionnaire pour stocker les informations sur les fichiers affichés

        # Création du panneau principal qui va contenir deux sections (arborescence et détails)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Création de la frame pour l'arborescence des dossiers (affichée à gauche)
        self.tree_frame = ttk.Frame(self.paned, width=300)
        # Création du widget Treeview pour afficher l'arborescence des dossiers
        self.tree = ttk.Treeview(self.tree_frame, show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.remplir_arborescence()                   # Remplit l'arborescence avec le dossier racine ou les lecteurs
        
        # Création de la frame de droite qui contiendra la liste des fichiers et les détails
        self.right_frame = ttk.Frame(self.paned)

        # Barre d'outils en haut de la partie droite : bouton retour, champ de saisie du chemin et case pour fichiers cachés
        self.toolbar = ttk.Frame(self.right_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Bouton "Retour" pour revenir au dossier parent
        self.back_button = ttk.Button(self.toolbar, text="Retour", command=self.go_back)
        self.back_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Champ de saisie pour entrer un chemin directement
        self.path_entry = ttk.Entry(self.toolbar)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.path_entry.bind('<Return>', self.navigate_to_path)  # Navigation vers le chemin saisi lors de l'appui sur "Entrée"
        
        # Variable pour la case à cocher qui détermine l'affichage des fichiers cachés
        self.show_hidden = tk.BooleanVar(value=False)
        self.hidden_checkbox = ttk.Checkbutton(self.toolbar, 
                                               text="Afficher fichiers cachés", 
                                               variable=self.show_hidden, 
                                               command=self.update_liste_fichier)  # Met à jour la liste lors du changement
        self.hidden_checkbox.pack(side=tk.LEFT, padx=(5,0))
        
        # Création du widget Treeview pour afficher la liste des fichiers avec plusieurs colonnes : taille, type, date modif.
        self.file_list = ttk.Treeview(self.right_frame, 
                                      columns=('size', 'type', 'modified'), 
                                      selectmode='browse')
        # Définition des en-têtes de colonnes et association à une fonction de tri pour chacune d'elles
        self.file_list.heading('#0', text='Nom', command=lambda: self.sort_column('name', False))
        self.file_list.heading('size', text='Taille', command=lambda: self.sort_column('size', False))
        self.file_list.heading('type', text='Type', command=lambda: self.sort_column('type', False))
        self.file_list.heading('modified', text='Modifié', command=lambda: self.sort_column('modified', False))
        # Configuration de la largeur de chaque colonne
        self.file_list.column('#0', width=250)
        self.file_list.column('size', width=100)
        self.file_list.column('type', width=150)
        self.file_list.column('modified', width=150)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        # Association d'événements sur la liste des fichiers
        self.file_list.bind('<Double-1>', self.on_file_double_click)    # Ouvrir ou naviguer lors d'un double clic
        self.file_list.bind('<<TreeviewSelect>>', self.on_file_select)    # Mettre à jour le panneau de détails lors de la sélection
        self.file_list.bind('<Button-3>', self.show_context_menu)         # Afficher le menu contextuel sur clic droit
        
        # Création du menu contextuel avec plusieurs actions (renommer, déplacer, créer, supprimer)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Renommer", command=self.inline_rename)
        self.context_menu.add_command(label="Déplacer", command=self.inline_move)
        self.context_menu.add_command(label="Créer un nouveau fichier", command=self.inline_create_file)
        self.context_menu.add_command(label="Supprimer", command=self.delete_selected_file)
        
        # Création du panneau de détails qui affiche des informations sur le fichier sélectionné
        self.details_frame = ttk.Frame(self.right_frame)
        self.details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Dictionnaire pour stocker les labels d'informations du panneau de détails
        self.details_labels = {}
        # Liste des informations à afficher avec un label et une clé associée
        details = [
            ('Chemin:', 'path'),
            ('Taille:', 'size'),
            ('Type:', 'type'),
            ('Créé le:', 'created'),
            ('Modifié le:', 'modified'),
        ]
        # Création des labels pour chaque information et positionnement dans la grille
        for i, (label_text, key) in enumerate(details):
            ttk.Label(self.details_frame, text=label_text).grid(row=i, column=0, sticky='e', padx=2, pady=2)
            value_label = ttk.Label(self.details_frame, text='')
            value_label.grid(row=i, column=1, sticky='w', padx=2, pady=2)
            self.details_labels[key] = value_label
        
        # Ajout des frames gauche et droite dans le panneau principal avec des poids de répartition
        self.paned.add(self.tree_frame, weight=1)
        self.paned.add(self.right_frame, weight=3)
        
        # Définition du chemin de départ (le dossier personnel de l'utilisateur)
        self.current_path = os.path.expanduser('~')
        self.update_champ_chemin_courant()               # Mise à jour du champ de saisie avec le chemin actuel
        self.update_liste_fichier()                # Affichage de la liste des fichiers du chemin actuel
        
        # Association d'événements pour l'arborescence (ouverture et sélection des nœuds)
        self.tree.bind('<<TreeviewOpen>>', self.ouverture_noeud)
        self.tree.bind('<<TreeviewSelect>>', self.selection_noeud)

    # Méthode pour remplir l'arborescence avec la racine ou les lecteurs Windows
    def remplir_arborescence(self):
        if platform.system() == 'Windows':      # Si le système est Windows
            for drive in self.recup_disques():
                # Ajout de chaque lecteur comme nœud racine
                node = self.tree.insert('', 'end', text=drive, values=[drive], tags=('directory',))
                # Ajout d'un nœud "dummy" pour permettre l'expansion (sera remplacé lors de l'ouverture)
                self.tree.insert(node, 'end', text='dummy')
        else:
            # Pour les systèmes non-Windows, le dossier racine est "/"
            root = '/'
            node = self.tree.insert('', 'end', text=root, values=[root], tags=('directory',))
            self.tree.insert(node, 'end', text='dummy')

    # Méthode pour récupérer la liste des lecteurs disponibles sous Windows
    def recup_disques(self):
        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f'{letter}:\\'
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    # Méthode appelée lors de l'ouverture d'un nœud de l'arborescence
    def ouverture_noeud(self, event):
        node = self.tree.focus()             # Récupère le nœud actuellement ouvert
        children = self.tree.get_children(node)
        # Si le premier enfant est le nœud "dummy", on le supprime et on remplit le nœud avec les sous-dossiers réels
        if children and self.tree.item(children[0], 'text') == 'dummy':
            self.tree.delete(children[0])
            path = self.tree.item(node, 'values')[0]
            self.remplir_noeud_arborescence(node, path)

    # Méthode pour remplir un nœud de l'arborescence avec ses sous-dossiers
    def remplir_noeud_arborescence(self, node, path):
        try:
            for entry in os.listdir(path):
                # Filtrer les fichiers cachés si nécessaire
                if not self.show_hidden.get() and entry.startswith('.'):
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):   # Vérifie si l'entrée est un dossier
                    child = self.tree.insert(node, 'end', text=entry, values=[full_path], tags=('directory',))
                    # Ajoute un nœud "dummy" pour permettre l'expansion ultérieure
                    self.tree.insert(child, 'end', text='dummy')
        except PermissionError:
            # Si l'accès au dossier est refusé, on passe (peut-être ajouter une gestion d'erreur)
            pass

    # Méthode appelée lors de la sélection d'un nœud dans l'arborescence
    def selection_noeud(self, event):
        node = self.tree.focus()             # Récupère le nœud sélectionné
        path = self.tree.item(node, 'values')[0]  # Récupère le chemin associé au nœud
        self.current_path = path             # Met à jour le chemin courant
        self.update_champ_chemin_courant()             # Met à jour le champ de saisie avec le nouveau chemin
        self.update_liste_fichier()              # Met à jour la liste des fichiers affichés

    # Méthode pour mettre à jour le champ de saisie du chemin avec le chemin courant
    def update_champ_chemin_courant(self):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.current_path)

    # Méthode pour mettre à jour la liste des fichiers dans le dossier courant
    def update_liste_fichier(self):
        # Suppression des éléments actuels de la liste
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        self.file_data = {}                  # Réinitialisation des données sur les fichiers
        try:
            entries = os.listdir(self.current_path)  # Récupère la liste des entrées dans le dossier courant
        except Exception:
            return
        
        dirs = []  # Liste pour les dossiers
        files = [] # Liste pour les fichiers
        for entry in entries:
            # Filtrer les fichiers cachés si nécessaire
            if not self.show_hidden.get() and entry.startswith('.'):
                continue
            full_path = os.path.join(self.current_path, entry)
            try:
                is_dir = os.path.isdir(full_path)  # Vérifie si l'entrée est un dossier
                stat_info = os.stat(full_path)     # Récupère les informations de statut (taille, dates, etc.)
                if is_dir:
                    dirs.append((entry, full_path, stat_info))
                else:
                    files.append((entry, full_path, stat_info))
            except Exception:
                continue
        
        # Trie et affichage des dossiers puis des fichiers
        for group in [dirs, files]:
            group.sort(key=lambda x: x[0].lower())
            for entry, full_path, stat_info in group:
                is_dir = os.path.isdir(full_path)
                size = stat_info.st_size if not is_dir else 0  # La taille est 0 pour les dossiers
                mtime = stat_info.st_mtime
                size_str = self.format_size(size)           # Formate la taille pour l'affichage
                # Formatage de la date de modification
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M:%S')
                type_str = 'Dossier' if is_dir else f"{os.path.splitext(entry)[1]} Fichier"
                # Insertion de l'entrée dans la liste avec les colonnes correspondantes
                item_id = self.file_list.insert('', 'end', text=entry, 
                                              values=(size_str, type_str, mtime_str),
                                              tags=('directory' if is_dir else 'file',))
                # Stockage des données détaillées dans le dictionnaire file_data
                self.file_data[item_id] = {
                    'path': full_path,
                    'size': size,
                    'type': type_str,
                    'mtime': mtime,
                    'ctime': stat_info.st_ctime
                }

    # Méthode pour formater la taille d'un fichier en octets, Ko, Mo, etc.
    def format_size(self, size):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        # Boucle pour déterminer l'unité appropriée
        while size >= 1024 and index < len(units)-1:
            size /= 1024
            index += 1
        return f"{size:.2f} {units[index]}" if index > 0 else f"{size} B"

    # Méthode appelée lors d'un double clic sur un fichier/dossier dans la liste
    def on_file_double_click(self, event):
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        entry = self.file_list.item(item, 'text')
        full_path = os.path.join(self.current_path, entry)
        # Si c'est un dossier, naviguer dans celui-ci
        if os.path.isdir(full_path):
            self.current_path = full_path
            self.update_champ_chemin_courant()
            self.update_liste_fichier()

    # Méthode pour trier les colonnes de la liste
    def sort_column(self, col, reverse):
        # Récupération de tous les items avec leur texte
        items = [(self.file_list.item(item, 'text'), item) for item in self.file_list.get_children('')]
        if col == 'name':
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        else:
            # Association des colonnes aux clés dans le dictionnaire file_data
            key_map = {'size': 'size', 'type': 'type', 'modified': 'mtime'}
            items.sort(key=lambda x: self.file_data[x[1]][key_map[col]], reverse=reverse)
        # Réorganisation des items dans la liste selon l'ordre trié
        for index, (text, item) in enumerate(items):
            self.file_list.move(item, '', index)
        # Mise à jour de la commande de l'en-tête pour inverser l'ordre au prochain clic
        self.file_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    # Méthode appelée lors de la sélection d'un fichier dans la liste pour afficher ses détails
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

    # Méthode pour naviguer vers un chemin entré dans le champ de saisie
    def navigate_to_path(self, event):
        path = self.path_entry.get()
        if os.path.exists(path):
            self.current_path = path
            self.update_liste_fichier()
        else:
            messagebox.showerror("Erreur", "Chemin introuvable")  # Affiche un message d'erreur si le chemin n'existe pas

    # Méthode pour revenir au dossier parent du chemin courant
    def go_back(self):
        parent = os.path.dirname(self.current_path)
        if parent and os.path.exists(parent) and parent != self.current_path:
            self.current_path = parent
            self.update_champ_chemin_courant()
            self.update_liste_fichier()

    # Méthode pour afficher le menu contextuel (clic droit) sur un élément de la liste
    def show_context_menu(self, event):
        item = self.file_list.identify_row(event.y)
        if item:
            self.file_list.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # Méthode pour renommer un fichier directement dans la liste (édition inline)
    def inline_rename(self):
        """Renommer directement le fichier en éditant le nom dans la liste."""
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        # Récupère la position de l'item pour placer l'éditeur
        bbox = self.file_list.bbox(item, '#0')
        if not bbox:
            return
        x, y, width, height = bbox
        # Création d'un champ de saisie pour renommer
        entry = ttk.Entry(self.file_list)
        entry.place(x=x, y=y, width=width, height=height)
        current_name = self.file_list.item(item, 'text')
        entry.insert(0, current_name)
        entry.focus_set()
        # Fonction interne pour valider le nouveau nom
        def on_rename(event=None):
            new_name = entry.get().strip()
            if new_name and new_name != current_name:
                full_old_path = os.path.join(self.current_path, current_name)
                full_new_path = os.path.join(self.current_path, new_name)
                try:
                    os.rename(full_old_path, full_new_path)
                    self.update_liste_fichier()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de renommer : {e}")
            entry.destroy()
        entry.bind('<Return>', on_rename)
        entry.bind('<FocusOut>', lambda event: entry.destroy())

    # Méthode pour déplacer un fichier en modifiant son chemin via le panneau de détails (édition inline)
    def inline_move(self):
        """Déplacer directement le fichier en modifiant son chemin dans le panneau de détails."""
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        data = self.file_data.get(item)
        if not data:
            return
        # Récupère la position du label du chemin pour placer l'éditeur
        label = self.details_labels['path']
        x = label.winfo_x()
        y = label.winfo_y()
        width = label.winfo_width() if label.winfo_width() > 100 else 200
        entry = ttk.Entry(self.details_frame)
        entry.place(x=x, y=y, width=width)
        entry.insert(0, data['path'])
        entry.focus_set()
        # Fonction interne pour déplacer le fichier
        def on_move(event=None):
            new_path = entry.get().strip()
            if new_path and new_path != data['path']:
                try:
                    os.rename(data['path'], new_path)
                    self.current_path = os.path.dirname(new_path)
                    self.update_champ_chemin_courant()
                    self.update_liste_fichier()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de déplacer le fichier : {e}")
            entry.destroy()
        entry.bind('<Return>', on_move)
        entry.bind('<FocusOut>', lambda event: entry.destroy())

    # Méthode pour créer un nouveau fichier en éditant directement son nom
    def inline_create_file(self):
        """Créer un nouveau fichier directement en éditant son nom."""
        # Positionne l'éditeur en haut de la liste (ou en haut à gauche si la liste est vide)
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
        # Fonction interne pour valider la création du fichier
        def on_create(event=None):
            filename = editor.get().strip()
            if filename:
                full_path = os.path.join(self.current_path, filename)
                try:
                    # Création d'un fichier vide en mode 'x' (lève une exception si le fichier existe déjà)
                    with open(full_path, 'x'):
                        pass
                    self.update_liste_fichier()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de créer le fichier : {e}")
            editor.destroy()
        editor.bind('<Return>', on_create)
        editor.bind('<FocusOut>', lambda event: editor.destroy())

    # Méthode pour supprimer le fichier ou dossier sélectionné
    def delete_selected_file(self):
        """Supprimer le fichier ou dossier sélectionné."""
        item = self.file_list.selection()
        if not item:
            return
        item = item[0]
        filename = self.file_list.item(item, 'text')
        full_path = os.path.join(self.current_path, filename)
        # Confirmation de suppression via une boîte de dialogue
        if messagebox.askyesno("Supprimer", f"Voulez-vous vraiment supprimer '{filename}' ?"):
            try:
                if os.path.isdir(full_path):
                    os.rmdir(full_path)   # Suppression d'un dossier (uniquement si vide)
                else:
                    os.remove(full_path)  # Suppression d'un fichier
                self.update_liste_fichier()   # Mise à jour de la liste après suppression
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer : {e}")

# Point d'entrée du programme : création et lancement de l'application
if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()  # Démarrage de la boucle principale de l'interface graphique