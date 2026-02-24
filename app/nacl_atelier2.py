"""
Atelier 2 – Chiffrement/Déchiffrement avec PyNaCl SecretBox
SecretBox utilise XSalsa20-Poly1305 :
  • XSalsa20 : chiffrement par flot (stream cipher) très rapide
  • Poly1305  : authentification du message (MAC) – garantit l'intégrité

La clé est de 32 octets (256 bits) encodée en hexadécimal.
Elle est chargée depuis la variable d'environnement NACL_KEY.

Usage :
    # Générer une nouvelle clé
    python app/nacl_atelier2.py genkey

    # Chiffrer
    export NACL_KEY="<hex-32-octets>"
    python app/nacl_atelier2.py encrypt secret.txt secret.enc

    # Déchiffrer
    python app/nacl_atelier2.py decrypt secret.enc secret.dec.txt
"""

import argparse
import os
import sys
from pathlib import Path

import nacl.secret
import nacl.utils
import nacl.exceptions


# ---------------------------------------------------------------------------
# Gestion de la clé
# ---------------------------------------------------------------------------

KEY_SIZE = nacl.secret.SecretBox.KEY_SIZE  # 32 octets


def generate_key() -> None:
    """Génère et affiche une nouvelle clé 256 bits encodée en hex."""
    key = nacl.utils.random(KEY_SIZE)
    hex_key = key.hex()
    print("🔑  Nouvelle clé NaCl SecretBox (256 bits, hex) :")
    print(hex_key)
    print("\n➡️  Exporter la clé :")
    print(f"    export NACL_KEY='{hex_key}'")
    print("    (ou l'ajouter comme Repository Secret GitHub sous NACL_KEY)")


def load_key_from_env() -> nacl.secret.SecretBox:
    """
    Charge la clé depuis NACL_KEY (hex).
    Dans GitHub Actions :
        env:
          NACL_KEY: ${{ secrets.NACL_KEY }}
    """
    hex_key = os.environ.get("NACL_KEY")
    if not hex_key:
        sys.exit(
            "❌  Variable NACL_KEY absente.\n"
            "    → Générer   : python app/nacl_atelier2.py genkey\n"
            "    → En local  : export NACL_KEY='<hex>'\n"
            "    → GitHub    : déclarez NACL_KEY comme Repository Secret"
        )
    try:
        key_bytes = bytes.fromhex(hex_key)
    except ValueError:
        sys.exit("❌  NACL_KEY n'est pas une chaîne hexadécimale valide.")

    if len(key_bytes) != KEY_SIZE:
        sys.exit(
            f"❌  NACL_KEY doit faire {KEY_SIZE} octets ({KEY_SIZE * 2} caractères hex), "
            f"reçu {len(key_bytes)} octets."
        )
    return nacl.secret.SecretBox(key_bytes)


# ---------------------------------------------------------------------------
# Opérations sur les fichiers
# ---------------------------------------------------------------------------

def encrypt_file(src: Path, dst: Path, box: nacl.secret.SecretBox) -> None:
    """
    Chiffre src et écrit le résultat dans dst.
    Le nonce (24 octets aléatoires) est automatiquement préfixé au ciphertext
    par PyNaCl – il est public et nécessaire au déchiffrement.
    """
    plaintext = src.read_bytes()
    encrypted = box.encrypt(plaintext)  # nonce (24 B) + ciphertext + MAC (16 B)
    dst.write_bytes(encrypted)
    print(f"✅  Chiffré   : {src}  →  {dst}")
    print(f"    Taille originale  : {len(plaintext)} octets")
    print(f"    Taille chiffrée   : {len(encrypted)} octets "
          f"(+{len(encrypted) - len(plaintext)} octets nonce+MAC)")


def decrypt_file(src: Path, dst: Path, box: nacl.secret.SecretBox) -> None:
    """
    Déchiffre src et écrit le résultat dans dst.
    Lève une erreur si le MAC est invalide (fichier altéré ou mauvaise clé).
    """
    ciphertext = src.read_bytes()
    try:
        plaintext = box.decrypt(ciphertext)
    except nacl.exceptions.CryptoError:
        sys.exit(
            "❌  Déchiffrement impossible.\n"
            "    Causes possibles :\n"
            "      • Mauvaise clé NACL_KEY\n"
            "      • Fichier chiffré altéré (MAC Poly1305 invalide)"
        )
    dst.write_bytes(plaintext)
    print(f"✅  Déchiffré : {src}  →  {dst}")


# ---------------------------------------------------------------------------
# Interface en ligne de commande
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atelier 2 – Chiffrement symétrique PyNaCl SecretBox"
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    sub.add_parser("genkey", help="Génère une nouvelle clé 256 bits")

    enc = sub.add_parser("encrypt", help="Chiffre un fichier")
    enc.add_argument("input",  help="Fichier source")
    enc.add_argument("output", help="Fichier chiffré")

    dec = sub.add_parser("decrypt", help="Déchiffre un fichier")
    dec.add_argument("input",  help="Fichier chiffré")
    dec.add_argument("output", help="Fichier déchiffré")

    args = parser.parse_args()

    if args.mode == "genkey":
        generate_key()
        return

    src = Path(args.input)
    dst = Path(args.output)

    if not src.exists():
        sys.exit(f"❌  Fichier introuvable : {src}")

    box = load_key_from_env()

    if args.mode == "encrypt":
        encrypt_file(src, dst, box)
    else:
        decrypt_file(src, dst, box)


if __name__ == "__main__":
    main()
