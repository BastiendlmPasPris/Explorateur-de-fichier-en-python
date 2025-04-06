import os
import time

import tkinter as tk

class FileManager(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Gestionnaire de fichiers")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Appel de la fonction principale
        self.main()

    def convertir_taille(self, size):
        """Convertit une taille en octets en une forme lisible."""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        while size >= 1024 and index < len(units)-1:
            size /= 1024
            index += 1
        return f"{size:.2f} {units[index]}"

    def lister_entree(self, current_dir):
        """Liste les entrées du répertoire avec leurs informations."""
        parent_entry = None
        if os.path.dirname(current_dir) != current_dir:
            parent_dir = os.path.normpath(os.path.join(current_dir, '..'))
            try:
                parent_entry = {
                    'name': '..',
                    'is_dir': True,
                    'size': 0,
                    'mod_date': os.path.getmtime(parent_dir)
                }
            except PermissionError:
                pass

        other_entries = []
        for name in os.listdir(current_dir):
            path = os.path.join(current_dir, name)
            is_dir = False
            size = 0
            mod_date = 0
            try:
                is_dir = os.path.isdir(path)
                if not is_dir:
                    size = os.path.getsize(path)
                mod_date = os.path.getmtime(path)
            except Exception as e:
                continue
            other_entries.append({
                'name': name,
                'is_dir': is_dir,
                'size': size,
                'mod_date': mod_date
            })
        
        return parent_entry, other_entries

    def trier_entree(self, entries, sort_by):
        """Trie les entrées selon le critère choisi."""
        if sort_by == 'name':
            return sorted(entries, key=lambda x: x['name'].lower())
        elif sort_by == 'size':
            return sorted(entries, key=lambda x: x['size'], reverse=True)
        elif sort_by == 'date':
            return sorted(entries, key=lambda x: x['mod_date'], reverse=True)
        elif sort_by == 'type':
            return sorted(entries, key=lambda x: (
                not x['is_dir'],
                os.path.splitext(x['name'])[1].lower(),
                x['name'].lower()
            ))
        return entries

    def main(self):
        self.mainloop()

        current_dir = os.getcwd()
        sort_by = 'name'
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            parent_entry, other_entries = self.lister_entree(current_dir)
            sorted_entries = self.trier_entree(other_entries, sort_by)
            
            entries = []
            if parent_entry:
                entries.append(parent_entry)
            entries.extend(sorted_entries)
            
            print(f"\nRépertoire actuel: {current_dir}")
            print("\n{:<5} {:<30} {:<10} {:<20} {}".format(
                "Num", "Nom", "Type", "Taille", "Modifié le"
            ))
            print("-" * 80)
            
            for idx, entry in enumerate(entries):
                file_type = "DIR" if entry['is_dir'] else "FILE"
                size = self.convertir_taille(entry['size']) if not entry['is_dir'] else "DIR"
                mod_date = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(entry['mod_date'])
                )
                print("{:<5} {:<30} {:<10} {:<20} {}".format(
                    idx+1, entry['name'], file_type, size, mod_date
                ))
            
            print("\nCommandes disponibles:")
            print("  :sort [name|size|date|type] - Trier les fichiers")
            print("  :back                      - Revenir au répertoire précédent")
            print("  :quit                      - Quitter")
            
            user_input = input("\nEntrez un numéro ou une commande: ").strip()
            
            if user_input.startswith(':'):
                cmd_parts = user_input[1:].split()
                if not cmd_parts:
                    continue
                
                if cmd_parts[0] == 'sort' and len(cmd_parts) > 1:
                    sort_by = cmd_parts[1]
                elif cmd_parts[0] == 'back':
                    new_dir = os.path.dirname(current_dir)
                    if os.path.isdir(new_dir):
                        current_dir = new_dir
                elif cmd_parts[0] == 'quit':
                    break
            else:
                try:
                    choice = int(user_input)
                    if 1 <= choice <= len(entries):
                        selected = entries[choice-1]
                        if selected['is_dir']:
                            new_dir = os.path.normpath(
                                os.path.join(current_dir, selected['name'])
                            )
                            if os.path.isdir(new_dir):
                                current_dir = new_dir
                        else:
                            input("\nAppuyez sur Entrée pour continuer...")
                except ValueError:
                    pass

if __name__ == "__main__":
    fenetre = FileManager()
