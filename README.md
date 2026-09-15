# Phénix Bank

Application mobile-first de gestion des amendes internes de l’équipe Phénix (saison 26/27). Elle démarre sans compte ni base en **mode démo**, avec 16 joueurs, leurs portraits et des données fictives conservées pendant la session.

## Installation et lancement

```bash
cd phenix-bank
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La partie publique ne demande aucun compte. Sans secret admin, un bouton explicite ouvre l’admin démo; les changements sont temporaires.

## Connexion Google Sheets avec Apps Script (recommandée)

Suivre [le guide Apps Script](apps-script/README.md) : installer le script dans le classeur, le déployer, puis renseigner son URL et sa clé dans les Secrets Streamlit. Aucun compte de service Google ni fichier JSON n’est nécessaire. Le mot de passe admin est obligatoire pour cette connexion.

## Configuration de production avec Supabase (alternative)

1. Créer un projet Supabase puis exécuter `supabase/schema.sql` et `supabase/seed.sql` dans le SQL Editor.
2. Copier `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml`.
3. Renseigner un mot de passe long, l’URL Supabase et la clé `service_role`.
4. Ne jamais versionner `secrets.toml`. La clé de service reste côté serveur Streamlit.

Pour remettre une saison Supabase à zéro, exécuter `supabase/reset_fines.sql`. Cette opération efface les paiements puis toutes les amendes, sans toucher aux joueurs ni aux règles.

Le schéma active la RLS : la lecture publique est autorisée et les écritures exigent la clé serveur. Dès que les secrets sont présents, l’application charge et modifie directement les tables Supabase; en cas d’absence de configuration, elle bascule automatiquement en mode démo.

## Médias

- Portraits : nommer les sources `Prenom.NOM_NUMERO.JPG` ou `.png`, puis lancer `python scripts/process_player_images.py`. L’application détecte automatiquement le numéro et utilise le PNG détouré 900×1100 généré dans `assets/players/cutouts/`. Une image absente est remplacée par un avatar.
- QR Wero : déposer le QR réel dans `assets/qr/wero.png`. Aucun lien de paiement n’est inventé; sa validation reste manuelle.
- Logo : les fichiers d’identité visuelle peuvent être placés dans `assets/logo/`.

## Déploiement Streamlit Community Cloud

Pousser le dossier sur GitHub, choisir `app.py` comme fichier principal, puis recopier le contenu de `secrets.toml` dans **App settings → Secrets**. Pour un dépôt dont la racine contient plusieurs projets, choisir `phenix-bank/app.py`.

## Architecture

- `app.py` : routage et vues responsives
- `components/` : navigation, cartes, podium, métriques, paiement Wero
- `services/` : données métier, amendes, paiements, authentification
- `utils/` : traductions, images, formatage
- `styles/main.css` : identité premium Phénix
- `supabase/` : schéma et règles initiales

Les paiements sont distincts des amendes. Le solde les impute au total dû du joueur, ce qui équivaut à une allocation FIFO tant qu’aucune ventilation détaillée par paiement n’est requise.

