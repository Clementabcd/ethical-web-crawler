import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import threading
import json
import csv
from datetime import datetime
import os
import webbrowser
from collections import deque
import re
import mimetypes

class EthicalWebCrawler:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Web Crawler Éthique v2.0")
        self.root.geometry("1000x800")
        
        # Configuration
        self.delay_between_requests = 1.0
        self.max_sites = 500
        self.timeout = 10
        self.max_depth = 3
        self.user_agent = "EthicalCrawler/2.0 (+https://example.com/bot)"
        
        # Données
        self.discovered_sites = []
        self.crawling = False
        self.paused = False
        self.start_urls = [
            "https://www.example.com",
            "https://httpbin.org",
            "https://jsonplaceholder.typicode.com"
        ]
        
        # Filtres simples
        self.blocked_domains = []
        self.blocked_keywords = []
        
        self.create_ui()
        
    def create_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration compacte
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Ligne 1
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X)
        
        ttk.Label(row1, text="Délai (sec):").pack(side=tk.LEFT)
        self.delay_var = tk.StringVar(value="1.0")
        ttk.Entry(row1, textvariable=self.delay_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(row1, text="Max sites:").pack(side=tk.LEFT)
        self.max_sites_var = tk.StringVar(value="500")
        ttk.Entry(row1, textvariable=self.max_sites_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(row1, text="Profondeur:").pack(side=tk.LEFT)
        self.max_depth_var = tk.StringVar(value="3")
        ttk.Entry(row1, textvariable=self.max_depth_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        self.respect_robots_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row1, text="Respecter robots.txt", variable=self.respect_robots_var).pack(side=tk.LEFT)
        
        # URLs de départ
        start_frame = ttk.LabelFrame(main_frame, text="URLs de départ", padding="10")
        start_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_urls_text = scrolledtext.ScrolledText(start_frame, height=4, width=80)
        self.start_urls_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.start_urls_text.insert(tk.END, "\n".join(self.start_urls))
        
        # Filtres rapides
        filter_frame = ttk.LabelFrame(main_frame, text="Filtres rapides", padding="5")
        filter_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        filter_row = ttk.Frame(filter_frame)
        filter_row.pack(fill=tk.X)
        
        ttk.Label(filter_row, text="Domaines bloqués:").pack(side=tk.LEFT)
        self.blocked_domains_var = tk.StringVar()
        ttk.Entry(filter_row, textvariable=self.blocked_domains_var, width=30).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(filter_row, text="Mots-clés bloqués:").pack(side=tk.LEFT)
        self.blocked_keywords_var = tk.StringVar()
        ttk.Entry(filter_row, textvariable=self.blocked_keywords_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # Boutons de contrôle
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="🚀 Démarrer", command=self.start_crawling)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.pause_button = ttk.Button(control_frame, text="⏸️ Pause", command=self.pause_crawling, state="disabled")
        self.pause_button.grid(row=0, column=1, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Arrêter", command=self.stop_crawling, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=(0, 10))
        
        self.clear_button = ttk.Button(control_frame, text="🗑️ Effacer", command=self.clear_results)
        self.clear_button.grid(row=0, column=3)
        
        # Statut et vitesse
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.progress_var = tk.StringVar(value="Prêt à démarrer")
        ttk.Label(status_frame, textvariable=self.progress_var).pack(side=tk.LEFT)
        
        self.speed_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.speed_var).pack(side=tk.RIGHT)
        
        # Barre de progression
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Résultats avec colonnes étendues
        results_frame = ttk.LabelFrame(main_frame, text="Sites découverts", padding="10")
        results_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Treeview amélioré
        columns = ("URL", "Titre", "Status", "Type", "Taille", "Temps", "Profondeur")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # Configuration des colonnes
        widths = {"URL": 350, "Titre": 200, "Status": 70, "Type": 100, "Taille": 80, "Temps": 80, "Profondeur": 80}
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=widths.get(col, 100))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Double-clic pour ouvrir URL
        self.results_tree.bind("<Double-1>", self.open_url_in_browser)
        
        # Menu contextuel
        self.create_context_menu()
        
        # Boutons d'export
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(export_frame, text="📄 JSON", command=lambda: self.export_results("json")).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(export_frame, text="📊 CSV", command=lambda: self.export_results("csv")).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(export_frame, text="📝 TXT", command=lambda: self.export_results("txt")).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(export_frame, text="📋 URLs", command=self.copy_urls).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(export_frame, text="📊 Stats", command=self.show_stats).grid(row=0, column=4)
        
        # Configuration de la grille
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
    
    def create_context_menu(self):
        """Menu contextuel pour les résultats"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🌐 Ouvrir dans le navigateur", command=self.open_selected_url)
        self.context_menu.add_command(label="📋 Copier URL", command=self.copy_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ Supprimer", command=self.delete_selected_item)
        
        self.results_tree.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        try:
            self.results_tree.selection_set(self.results_tree.identify_row(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def open_url_in_browser(self, event):
        self.open_selected_url()
        
    def open_selected_url(self):
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            url = item['values'][0]
            webbrowser.open(url)
            
    def copy_selected_url(self):
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            url = item['values'][0]
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            
    def delete_selected_item(self):
        selection = self.results_tree.selection()
        if selection:
            self.results_tree.delete(selection[0])
    
    def copy_urls(self):
        """Copie toutes les URLs"""
        urls = [self.results_tree.item(item)['values'][0] for item in self.results_tree.get_children()]
        if urls:
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(urls))
            messagebox.showinfo("Info", f"{len(urls)} URLs copiées")
    
    def check_robots_txt(self, url):
        """Vérifie robots.txt avec cache simple"""
        if not self.respect_robots_var.get():
            return True
        
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if not hasattr(self, 'robots_cache'):
                self.robots_cache = {}
                
            if base_url not in self.robots_cache:
                try:
                    rp = RobotFileParser()
                    rp.set_url(f"{base_url}/robots.txt")
                    rp.read()
                    self.robots_cache[base_url] = rp
                except:
                    self.robots_cache[base_url] = None
            
            rp = self.robots_cache[base_url]
            return rp.can_fetch(self.user_agent, url) if rp else True
        except:
            return True
    
    def detect_content_type(self, response):
        """Détection simple du type de contenu"""
        content_type = response.headers.get('content-type', '').lower()
        
        if 'text/html' in content_type:
            return 'HTML', '🌐'
        elif 'application/json' in content_type:
            return 'JSON', '📋'
        elif 'text/css' in content_type:
            return 'CSS', '🎨'
        elif 'javascript' in content_type:
            return 'JS', '⚡'
        elif 'image/' in content_type:
            return 'Image', '🖼️'
        elif 'application/pdf' in content_type:
            return 'PDF', '📄'
        else:
            return 'Autre', '❓'
    
    def apply_filters(self, url, title):
        """Application des filtres"""
        domain = urlparse(url).netloc
        
        # Domaines bloqués
        blocked_domains = [d.strip() for d in self.blocked_domains_var.get().split(',') if d.strip()]
        if any(bd in domain for bd in blocked_domains):
            return False
        
        # Mots-clés bloqués
        blocked_keywords = [k.strip().lower() for k in self.blocked_keywords_var.get().split(',') if k.strip()]
        text_check = f"{url.lower()} {title.lower()}"
        if any(kw in text_check for kw in blocked_keywords):
            return False
        
        return True
    
    def extract_links(self, html_content, base_url):
        """Extraction des liens améliorée"""
        links = []
        try:
            # Liens href
            href_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
            href_matches = re.findall(href_pattern, html_content, re.IGNORECASE)
            
            for match in href_matches:
                try:
                    full_url = urljoin(base_url, match)
                    if full_url.startswith(('http://', 'https://')):
                        # Nettoyer l'URL
                        parsed = urlparse(full_url)
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            clean_url += f"?{parsed.query}"
                        links.append(clean_url)
                except:
                    continue
        except:
            pass
        
        return list(set(links))[:20]  # Max 20 liens par page
    
    def get_page_title(self, html_content):
        """Extraction du titre"""
        try:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                return title_match.group(1).strip()[:100]
        except:
            pass
        return "Sans titre"
    
    def format_size(self, size_bytes):
        """Formatage de la taille"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024**2):.1f}MB"
    
    def crawl_site(self, url, depth=0):
        """Crawling d'un site avec détection de contenu"""
        try:
            if not self.check_robots_txt(url):
                return None, [], "Bloqué par robots.txt"
            
            headers = {'User-Agent': self.user_agent}
            start_time = time.time()
            
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000)
            
            # Détection du type
            content_type, type_icon = self.detect_content_type(response)
            
            # Extraction du titre
            title = "Non-HTML"
            new_links = []
            
            if 'text/html' in response.headers.get('content-type', '').lower():
                try:
                    html_content = response.text
                    title = self.get_page_title(html_content)
                    
                    # Extraction des liens si on n'a pas atteint la profondeur max
                    if depth < int(self.max_depth_var.get()):
                        new_links = self.extract_links(html_content, url)
                except:
                    pass
            
            # Application des filtres
            if not self.apply_filters(url, title):
                return None, [], "Filtré"
            
            # Informations du site
            site_info = {
                'url': url,
                'title': title,
                'status': response.status_code,
                'content_type': content_type,
                'type_icon': type_icon,
                'size': len(response.content),
                'size_formatted': self.format_size(len(response.content)),
                'response_time': response_time,
                'depth': depth,
                'timestamp': datetime.now().isoformat()
            }
            
            return site_info, new_links, None
            
        except requests.exceptions.RequestException as e:
            return None, [], f"Erreur: {str(e)[:30]}"
    
    def crawling_worker(self):
        """Worker de crawling optimisé"""
        try:
            self.delay_between_requests = float(self.delay_var.get())
            self.max_sites = int(self.max_sites_var.get())
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs de configuration invalides")
            self.stop_crawling()
            return
        
        start_urls = [url.strip() for url in self.start_urls_text.get(1.0, tk.END).split('\n') if url.strip()]
        
        if not start_urls:
            messagebox.showerror("Erreur", "Aucune URL de départ")
            self.stop_crawling()
            return
        
        # Queue BFS avec profondeur
        url_queue = deque()
        for url in start_urls:
            url_queue.append((url, 0))  # (url, depth)
        
        visited_urls = set()
        sites_crawled = 0
        start_time = time.time()
        
        while url_queue and self.crawling and sites_crawled < self.max_sites:
            # Pause si demandée
            while self.paused and self.crawling:
                time.sleep(0.1)
            
            if not self.crawling:
                break
            
            current_url, depth = url_queue.popleft()
            
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            # Mise à jour du statut
            progress = (sites_crawled / self.max_sites) * 100
            elapsed = time.time() - start_time
            speed = sites_crawled / elapsed if elapsed > 0 else 0
            
            self.root.after(0, lambda: self.update_status(current_url, sites_crawled, self.max_sites, speed, progress))
            
            # Crawl du site
            site_info, new_links, error = self.crawl_site(current_url, depth)
            
            if site_info:
                self.discovered_sites.append(site_info)
                self.root.after(0, lambda info=site_info: self.add_result_to_tree(info))
                
                # Ajouter les liens à la queue
                for link in new_links:
                    if link not in visited_urls and len(url_queue) < 1000:  # Limite la queue
                        url_queue.append((link, depth + 1))
                
                sites_crawled += 1
            
            # Délai entre requêtes
            if self.crawling:
                time.sleep(self.delay_between_requests)
        
        # Fin du crawling
        self.root.after(0, self.crawling_finished)
    
    def update_status(self, url, crawled, total, speed, progress):
        """Mise à jour du statut"""
        short_url = url[:50] + "..." if len(url) > 50 else url
        self.progress_var.set(f"Crawling: {short_url} ({crawled}/{total})")
        self.speed_var.set(f"{speed:.1f} sites/sec")
        self.progress_bar['value'] = progress
    
    def add_result_to_tree(self, site_info):
        """Ajout d'un résultat au tree"""
        values = (
            site_info['url'],
            site_info['title'],
            f"{site_info['status']} {'✅' if site_info['status'] == 200 else '⚠️'}",
            f"{site_info['type_icon']} {site_info['content_type']}",
            site_info['size_formatted'],
            f"{site_info['response_time']}ms",
            f"Niv.{site_info['depth']}"
        )
        
        item = self.results_tree.insert("", tk.END, values=values)
        self.results_tree.see(item)
    
    def start_crawling(self):
        """Démarrage du crawling"""
        self.crawling = True
        self.paused = False
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.progress_bar['mode'] = 'determinate'
        self.progress_bar['value'] = 0
        
        self.crawling_thread = threading.Thread(target=self.crawling_worker, daemon=True)
        self.crawling_thread.start()
    
    def pause_crawling(self):
        """Pause/reprendre"""
        if self.crawling:
            self.paused = not self.paused
            self.pause_button.config(text="▶️ Reprendre" if self.paused else "⏸️ Pause")
    
    def stop_crawling(self):
        """Arrêt du crawling"""
        self.crawling = False
        self.paused = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="⏸️ Pause")
        self.stop_button.config(state="disabled")
        self.progress_var.set("Crawling arrêté")
        self.speed_var.set("")
    
    def crawling_finished(self):
        """Fin du crawling"""
        self.crawling = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="⏸️ Pause")
        self.stop_button.config(state="disabled")
        
        total = len(self.discovered_sites)
        self.progress_var.set(f"✅ Terminé! {total} sites découverts")
        self.speed_var.set("")
    
    def clear_results(self):
        """Effacement des résultats"""
        if self.discovered_sites and messagebox.askyesno("Confirmer", f"Effacer {len(self.discovered_sites)} résultats ?"):
            self.discovered_sites.clear()
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            self.progress_var.set("Résultats effacés")
            self.progress_bar['value'] = 0
    
    def show_stats(self):
        """Affichage des statistiques"""
        if not self.discovered_sites:
            messagebox.showinfo("Stats", "Aucune donnée à analyser")
            return
        
        # Calculs des stats
        total = len(self.discovered_sites)
        domains = {}
        status_codes = {}
        content_types = {}
        
        for site in self.discovered_sites:
            domain = urlparse(site['url']).netloc
            domains[domain] = domains.get(domain, 0) + 1
            status_codes[site['status']] = status_codes.get(site['status'], 0) + 1
            content_types[site['content_type']] = content_types.get(site['content_type'], 0) + 1
        
        # Fenêtre des stats
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Statistiques")
        stats_window.geometry("600x500")
        
        text_area = scrolledtext.ScrolledText(stats_window, font=('Courier', 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        stats_text = f"""📊 STATISTIQUES DE CRAWLING

🌐 RÉSUMÉ:
   • Total de sites: {total}
   • Domaines uniques: {len(domains)}

🏆 TOP DOMAINES:"""
        
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            stats_text += f"\n   • {domain}: {count} pages"
        
        stats_text += f"\n\n📊 CODES DE STATUT:"
        for status, count in sorted(status_codes.items()):
            percentage = (count / total) * 100
            stats_text += f"\n   • {status}: {count} ({percentage:.1f}%)"
        
        stats_text += f"\n\n🏷️ TYPES DE CONTENU:"
        for content_type, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            stats_text += f"\n   • {content_type}: {count} ({percentage:.1f}%)"
        
        text_area.insert(tk.END, stats_text)
        text_area.config(state='disabled')
    
    def export_results(self, format_type):
        """Export des résultats (BUG CORRIGÉ)"""
        if not self.discovered_sites:
            messagebox.showwarning("Attention", "Aucun résultat à exporter")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if format_type == "json":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    initialname=f"crawl_results_{timestamp}.json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.discovered_sites, f, indent=2, ensure_ascii=False)
                    messagebox.showinfo("Succès", f"✅ Exporté: {filename}")
            
            elif format_type == "csv":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    initialname=f"crawl_results_{timestamp}.csv",  
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )
                if filename:
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        fieldnames = ['url', 'title', 'status', 'content_type', 'size', 'response_time', 'depth', 'timestamp']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for site in self.discovered_sites:
                            row = {k: site.get(k, '') for k in fieldnames}
                            writer.writerow(row)
                    messagebox.showinfo("Succès", f"✅ Exporté: {filename}")
            
            elif format_type == "txt":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    initialname=f"crawl_results_{timestamp}.txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                )
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"🕷️ Résultats du Web Crawling - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("="*80 + "\n\n")
                        
                        for i, site in enumerate(self.discovered_sites, 1):
                            f.write(f"[{i}] {site['url']}\n")
                            f.write(f"    Titre: {site['title']}\n")
                            f.write(f"    Status: {site['status']}\n")
                            f.write(f"    Type: {site['content_type']}\n")
                            f.write(f"    Taille: {site['size_formatted']}\n")
                            f.write(f"    Temps: {site['response_time']}ms\n")
                            f.write(f"    Profondeur: {site['depth']}\n")
                            f.write("-" * 60 + "\n")
                    messagebox.showinfo("Succès", f"✅ Exporté: {filename}")
        
        except PermissionError:
            messagebox.showerror("Erreur", "❌ Fichier en cours d'utilisation ou permissions insuffisantes")
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur d'export: {str(e)}")
    
    def run(self):
        """Lance l'application"""
        # Gestionnaire de fermeture
        def on_closing():
            if self.crawling:
                if messagebox.askokcancel("Quitter", "Crawling en cours. Quitter quand même ?"):
                    self.stop_crawling()
                    time.sleep(0.5)
                    self.root.destroy()
            else:
                self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    print("🚀 Web Crawler Éthique v2.0 - Design Original + Nouvelles Fonctionnalités")
    print("=" * 70)
    
    app = EthicalWebCrawler()
    app.run()