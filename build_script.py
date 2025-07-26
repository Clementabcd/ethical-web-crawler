import subprocess
import sys
import os

def install_requirements():
    """Installe les dépendances"""
    print("Installation des dépendances...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """Compile l'application en exécutable"""
    print("Compilation de l'application...")
    
    # Commande PyInstaller avec options optimisées
    cmd = [
        "pyinstaller",
        "--onefile",                    # Un seul fichier exécutable
        "--windowed",                   # Pas de console (pour GUI)
        "--name=WebCrawlerEthique",     # Nom de l'exécutable
        "--icon=icon.ico",              # Icône (optionnel)
        "--add-data=README.md;.",       # Inclure des fichiers additionnels
        "web_crawler.py"                # Fichier principal
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ Compilation réussie!")
        print("L'exécutable se trouve dans le dossier 'dist/'")
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de la compilation")
        # Essayer sans l'icône si elle n'existe pas
        cmd_no_icon = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=WebCrawlerEthique",
            "web_crawler.py"
        ]
        try:
            subprocess.check_call(cmd_no_icon)
            print("✅ Compilation réussie (sans icône)!")
        except:
            print("❌ Compilation échouée")

if __name__ == "__main__":
    print("🚀 Script de build pour Web Crawler Éthique")
    print("=" * 50)
    
    install_requirements()
    build_executable()
    
    print("\nPour exécuter manuellement:")
    print("1. pip install -r requirements.txt")
    print("2. pip install pyinstaller")
    print("3. pyinstaller --onefile --windowed --name=WebCrawlerEthique web_crawler.py")
