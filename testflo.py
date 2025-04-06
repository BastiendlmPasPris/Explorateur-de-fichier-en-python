import os
import time
import tkinter as tk
from tkinter import ttk, messagebox

class GestionnaireFichiers(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestionnaire de fichiers")
        self.geometry("800x410")
        self.repertoire_actuel = os.getcwd()
        self.ordre_tri = 'nom'
        
        # Configuration du style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Treeview', hauteur_ligne=25)
        
        # Création des éléments d'interface
        self.creer_widgets()
        self.mettre_a_jour_liste()

    def creer_widgets(self):
        """Crée l'interface graphique"""
        # Cadre principal
        cadre_principal = ttk.Frame(self)
        cadre_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Étiquette et champ du chemin
        self.etiquette_chemin = ttk.Label(cadre_principal, text="Répertoire actuel :")
        self.etiquette_chemin.grid(row=0, column=0, sticky='w')
        
        self.var_chemin = tk.StringVar()
        self.entree_chemin = ttk.Entry(cadre_principal, textvariable=self.var_chemin, width=80)
        self.entree_chemin.grid(row=0, column=1, sticky='ew', padx=5)
        
        # Contrôles de navigation
        cadre_controles = ttk.Frame(cadre_principal)
        cadre_controles.grid(row=0, column=2, sticky='e')
        
        self.bouton_retour = ttk.Button(cadre_controles, text="Retour", command=self.retour_arriere)
        self.bouton_retour.pack(side=tk.LEFT, padx=2)
        
        self.liste_tri = ttk.Combobox(cadre_controles, values=['Nom', 'Taille', 'Date', 'Type'], state='lecture_seule')
        self.liste_tri.set('Nom')
        self.liste_tri.pack(side=tk.LEFT, padx=2)
        self.liste_tri.bind('<<ComboboxSelected>>', self.changer_tri)
        
        # Liste des fichiers
        self.arbre = ttk.Treeview(cadre_principal, columns=('type', 'taille', 'modification'), selectmode='browse', height=16)
        self.arbre.heading('#0', text='Nom', anchor='w')
        self.arbre.heading('type', text='Type')
        self.arbre.heading('taille', text='Taille')
        self.arbre.heading('modification', text='Modifié le')
        
        self.arbre.column('#0', width=300, anchor='w')
        self.arbre.column('type', width=100, anchor='center')
        self.arbre.column('taille', width=100, anchor='center')
        self.arbre.column('modification', width=200, anchor='center')
        
        self.arbre.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=10)
        self.arbre.bind('<Double-1>', self.double_clic)
        
        # Configuration du redimensionnement
        cadre_principal.columnconfigure(1, weight=1)
        cadre_principal.columnconfigure(1, weight=1)

    def convertir_taille(self, taille):
        """Convertit une taille en octets en une forme lisible"""
        unites = ['o', 'Ko', 'Mo', 'Go', 'To']
        index = 0
        while taille >= 1024 and index < len(unites)-1:
            taille /= 1024
            index += 1
        return f"{taille:.2f} {unites[index]}" if index > 0 else f"{taille} o"

    def lister_contenu(self, repertoire):
        """Liste le contenu d'un répertoire"""
        elements = []
        
        # Ajout du dossier parent
        if os.path.dirname(repertoire) != repertoire:
            dossier_parent = os.path.normpath(os.path.join(repertoire, '..'))
            try:
                elements.append({
                    'nom': '..',
                    'chemin': dossier_parent,
                    'dossier': True,
                    'taille': 0,
                    'date_modif': os.path.getmtime(dossier_parent)
                })
            except PermissionError:
                pass

        # Ajout des autres éléments
        for nom in os.listdir(repertoire):
            chemin = os.path.join(repertoire, nom)
            try:
                est_dossier = os.path.isdir(chemin)
                taille = os.path.getsize(chemin) if not est_dossier else 0
                date_modif = os.path.getmtime(chemin)
                elements.append({
                    'nom': nom,
                    'chemin': chemin,
                    'dossier': est_dossier,
                    'taille': taille,
                    'date_modif': date_modif
                })
            except Exception:
                continue
        
        return elements

    def trier_elements(self, elements):
        """Trie les éléments selon le critère sélectionné"""
        cle_tri = self.liste_tri.get().lower()
        if cle_tri == 'nom':
            return sorted(elements, key=lambda x: x['nom'].lower())
        elif cle_tri == 'taille':
            return sorted(elements, key=lambda x: x['taille'], reverse=True)
        elif cle_tri == 'date':
            return sorted(elements, key=lambda x: x['date_modif'], reverse=True)
        elif cle_tri == 'type':
            return sorted(elements, key=lambda x: (
                not x['dossier'],
                os.path.splitext(x['nom'])[1].lower(),
                x['nom'].lower()
            ))
        return elements

    def mettre_a_jour_liste(self):
        """Met à jour l'affichage de la liste"""
        # Vidage de l'arbre
        self.arbre.delete(*self.arbre.get_children())
        
        # Mise à jour du chemin
        self.var_chemin.set(self.repertoire_actuel)
        
        # Récupération et tri des éléments
        elements = self.lister_contenu(self.repertoire_actuel)
        elements_tries = self.trier_elements(elements)
        
        # Ajout des éléments à l'interface
        for element in elements_tries:
            type_element = 'Dossier' if element['dossier'] else 'Fichier'
            taille = self.convertir_taille(element['taille']) if not element['dossier'] else ''
            date_modif = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(element['date_modif']))
            
            self.arbre.insert('', 'end', 
                            text=element['nom'],
                            values=(type_element, taille, date_modif),
                            tags=('dossier' if element['dossier'] else 'fichier'))

    def double_clic(self, evenement):
        """Gère le double-clic sur un élément"""
        element = self.arbre.selection()[0]
        donnees = self.arbre.item(element)
        nom = donnees['text']
        
        if donnees['values'][0] == 'Dossier':
            nouveau_chemin = os.path.normpath(os.path.join(self.repertoire_actuel, nom))
            if os.path.isdir(nouveau_chemin):
                self.repertoire_actuel = nouveau_chemin
                self.mettre_a_jour_liste()
            elif nom == '..':
                self.repertoire_actuel = os.path.dirname(self.repertoire_actuel)
                self.mettre_a_jour_liste()

    def retour_arriere(self):
        """Retour au répertoire parent"""
        dossier_parent = os.path.dirname(self.repertoire_actuel)
        if os.path.isdir(dossier_parent):
            self.repertoire_actuel = dossier_parent
            self.mettre_a_jour_liste()

    def changer_tri(self, evenement):
        """Change le critère de tri"""
        self.mettre_a_jour_liste()

if __name__ == "__main__":
    application = GestionnaireFichiers()
    application.mainloop()