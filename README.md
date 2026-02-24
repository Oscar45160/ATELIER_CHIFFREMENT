# Atelier – Chiffrement/Déchiffrement (Python `cryptography`) dans GitHub Codespaces

## 1) Lancer le projet dans Codespaces
- Fork / clone ce repo
- Bouton **Code** → **Create codespace on main**

## 2) Installer les bibliothèques Python
```bash
pip install -r requirements.txt
```
> Les dépendances incluent `cryptography` (Fernet) et `pynacl` (SecretBox).

---

## 3) Partie A – Chiffrer/Déchiffrer un texte
```bash
python app/fernet_demo.py
```
**Quel est le rôle de la clé Fernet ?**  
La clé Fernet est une clé symétrique secrète de 256 bits encodée en Base64, utilisée pour chiffrer et authentifier les données avec AES et HMAC issue de la bibliothèque python cryptography. Un token Fernet (le résultat chiffré) contient :

```
| Version (1 B) | Timestamp (8 B) | IV (16 B) | Ciphertext (variable) | HMAC (32 B) |
```

| Champ | Taille | Rôle |
|---|---|---|
| Version | 1 octet | Valeur actuelle : `0x80` |
| Timestamp | 8 octets | Permet l'expiration des tokens |
| IV | 16 octets | Généré aléatoirement – garantit que deux messages identiques produisent des ciphertexts différents |
| Ciphertext | variable | Résultat du chiffrement AES-128-CBC |
| HMAC | 32 octets | Protège contre toute modification (intégrité + authenticité) |

---

## 4) Partie B – Chiffrer/Déchiffrer un fichier
Créer un fichier de test :
```bash
echo "Message Top secret !" > secret.txt
```
Chiffrer :
```bash
python app/file_crypto.py encrypt secret.txt secret.enc
```
Déchiffrer :
```bash
python app/file_crypto.py decrypt secret.enc secret.dec.txt
cat secret.dec.txt
```

**Que se passe-t-il si on modifie un octet du fichier chiffré ?**  
Fernet intègre un HMAC-SHA256 qui couvre l'intégralité du token (IV + ciphertext). Si un seul octet est modifié, la vérification du HMAC échoue au moment du déchiffrement et Python lève une exception `cryptography.fernet.InvalidToken`. **Il est impossible de déchiffrer un fichier altéré**, même partiellement. C'est le principe d'**authenticité** : toute modification est détectée.

**Pourquoi ne faut-il pas commiter la clé dans Git ?**  
Une clé commitée dans Git est **exposée pour toujours** : l'historique Git est immuable et la clé reste accessible même après suppression du fichier. N'importe qui ayant accès au dépôt (y compris des forks ou des clones anciens) peut alors déchiffrer tous les fichiers protégés par cette clé. Il faut stocker les secrets dans des **variables d'environnement** ou des **secrets gestionnaires** (GitHub Secrets, Vault, etc.) et les ajouter à `.gitignore`.

---

## 5) Atelier 1 – Fernet avec Secret GitHub
**Script :** `app/fernet_atelier1.py`

La clé Fernet n'est plus générée dans le code : elle est lue depuis la variable d'environnement `FERNET_KEY`, déclarée comme **Repository Secret** GitHub.

### Configuration du Secret GitHub
1. Générer une clé :
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
2. Dans GitHub : **Settings → Secrets and variables → Actions → New repository secret**
   - Nom : `FERNET_KEY`
   - Valeur : la clé générée ci-dessus

### Utilisation en local
```bash
export FERNET_KEY="<votre-clé-base64>"
python app/fernet_atelier1.py encrypt secret.txt secret.enc
python app/fernet_atelier1.py decrypt secret.enc secret.dec.txt
```

### Exemple de workflow GitHub Actions
```yaml
- name: Chiffrer un fichier
  env:
    FERNET_KEY: ${{ secrets.FERNET_KEY }}
  run: python app/fernet_atelier1.py encrypt secret.txt secret.enc
```

---

## 6) Atelier 2 – Chiffrement PyNaCl SecretBox
**Script :** `app/nacl_atelier2.py`

`SecretBox` de PyNaCl utilise **XSalsa20-Poly1305** :
- **XSalsa20** : chiffrement par flot (stream cipher), résistant aux nonces réutilisés
- **Poly1305** : MAC (Message Authentication Code) – garantit l'intégrité
- La clé est de **32 octets (256 bits)**, stockée en hexadécimal dans `NACL_KEY`

### Comparaison Fernet vs SecretBox

| | Fernet | PyNaCl SecretBox |
|---|---|---|
| Algorithme | AES-128-CBC + HMAC-SHA256 | XSalsa20 + Poly1305 |
| Taille de clé | 256 bits | 256 bits |
| Nonce | IV 16 B (CBC) | Nonce 24 B aléatoire |
| Overhead | ~57 B | 40 B (nonce 24 B + MAC 16 B) |
| Timestamp | ✅ (expiration possible) | ❌ |
| Facilité d'usage | ✅ Très simple | ✅ Très simple |

### Utilisation
```bash
# 1. Générer une clé
python app/nacl_atelier2.py genkey

# 2. Exporter la clé
export NACL_KEY="<hex-64-caractères>"

# 3. Chiffrer
python app/nacl_atelier2.py encrypt secret.txt secret.enc

# 4. Déchiffrer
python app/nacl_atelier2.py decrypt secret.enc secret.dec.txt
```





