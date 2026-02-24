"""
Atelier 1 – Chiffrement/Déchiffrement avec Fernet
La clé Fernet n'est pas générée dans le code : elle est lue depuis
la variable d'environnement FERNET_KEY, qui doit être définie comme
Secret GitHub (ou variable d'environnement locale pour les tests).

Usage :
    export FERNET_KEY="<votre-clé-base64>"
    python app/fernet_atelier1.py encrypt secret.txt secret.enc
    python app/fernet_atelier1.py decrypt secret.enc secret.dec.txt
"""

import argparse
import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken


# ---------------------------------------------------------------------------
# Chargement de la clé depuis l'environnement (Secret GitHub ou .env local)
# ---------------------------------------------------------------------------

def load_key_from_env() -> Fernet:
    """
    Charge la clé Fernet depuis la variable d'environnement FERNET_KEY.
    Dans un workflow GitHub Actions, cette variable doit être déclarée comme
    Repository Secret et injectée via :
        env:
          FERNET_KEY: ${{ secrets.FERNET_KEY }}
    En local, exporter la variable avant d'exécuter le script :
        export FERNET_KEY="<clé>"
    """
    key = os.environ.get("FERNET_KEY")
    if not key:
        sys.exit(
            "❌  Variable FERNET_KEY absente.\n"
            "    → En local  : export FERNET_KEY='<clé>'\n"
            "    → GitHub    : déclarez FERNET_KEY comme Repository Secret\n"
            "    → Générer   : python -c "
            "\"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode())
    except Exception as exc:
        sys.exit(f"❌  Clé FERNET_KEY invalide : {exc}")


# ---------------------------------------------------------------------------
# Opérations sur les fichiers
# ---------------------------------------------------------------------------

def encrypt_file(src: Path, dst: Path, fernet: Fernet) -> None:
    token = fernet.encrypt(src.read_bytes())
    dst.write_bytes(token)
    print(f"✅  Chiffré   : {src}  →  {dst}")


def decrypt_file(src: Path, dst: Path, fernet: Fernet) -> None:
    try:
        data = fernet.decrypt(src.read_bytes())
    except InvalidToken:
        sys.exit(
            "❌  Déchiffrement impossible.\n"
            "    Causes possibles :\n"
            "      • Mauvaise clé FERNET_KEY\n"
            "      • Fichier chiffré altéré (intégrité HMAC violée)"
        )
    dst.write_bytes(data)
    print(f"✅  Déchiffré : {src}  →  {dst}")


# ---------------------------------------------------------------------------
# Interface en ligne de commande
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atelier 1 – Chiffrement Fernet via Secret GitHub"
    )
    parser.add_argument("mode", choices=["encrypt", "decrypt"],
                        help="Mode : encrypt ou decrypt")
    parser.add_argument("input",  help="Fichier source")
    parser.add_argument("output", help="Fichier destination")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    if not src.exists():
        sys.exit(f"❌  Fichier introuvable : {src}")

    fernet = load_key_from_env()

    if args.mode == "encrypt":
        encrypt_file(src, dst, fernet)
    else:
        decrypt_file(src, dst, fernet)


if __name__ == "__main__":
    main()
