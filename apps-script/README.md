# Connecter Phénix Bank avec Apps Script

## 1. Installer le script
Dans le Google Sheet existant, ouvrir **Extensions → Apps Script** et remplacer le contenu de `Code.gs` par celui de [Code.gs](Code.gs). Enregistrer.
Les quatre onglets et leurs en-têtes doivent correspondre à ceux du fichier « Phénix Bank — Base de données 26-27 ».

## 2. Configurer les propriétés
Dans Apps Script, ouvrir **Paramètres du projet → Propriétés du script** :
- `SPREADSHEET_ID` : `1aTGbjmn1_8ooRln6gwrMudfD6G34HVZe86rILk7o_U4`
- `API_KEY` : une clé aléatoire d'au moins 32 caractères.

Pour générer la clé sur ton Mac : `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`.
Conserver cette clé uniquement dans les propriétés du script et les Secrets Streamlit.

## 3. Déployer
**Déployer → Nouveau déploiement → Application Web**.
- Exécuter en tant que : **Moi**
- Qui a accès : **Tout le monde**
Autoriser l'accès à ton classeur puis copier l'URL terminant par `/exec`.
Le compte Google peut imposer des restrictions de déploiement : si « Tout le monde » est absent, vérifier la politique du compte.
L'endpoint est accessible sans connexion Google mais chaque requête, y compris la lecture, exige la clé serveur. Le Sheet peut rester privé.
Référence : https://developers.google.com/apps-script/guides/web

## 4. Configurer Streamlit
Dans **Settings → Secrets**, remplacer les anciennes sections de connexion par :

```toml
[admin]
password = "TON_MOT_DE_PASSE_ADMIN_LONG"

[apps_script]
url = "URL_DU_DEPLOIEMENT_TERMINANT_PAR_EXEC"
api_key = "LA_MEME_CLE_QUE_DANS_APPS_SCRIPT"
```

Conserver le mot de passe admin existant si déjà configuré. Enregistrer et redémarrer l'app.
Le badge **GOOGLE SHEETS** apparaît après une lecture réussie.
Une configuration Apps Script incomplète ou inaccessible bloque l'app avec une erreur explicite, sans basculer en démo.
Les données sont relues à chaque interaction avec l'app ; une session ouverte doit interagir ou recharger pour voir les nouveautés.

## 5. Vérifier
Se connecter à l'admin, ajouter une amende test et vérifier sa ligne dans **Amendes**.
Ouvrir le site dans une nouvelle fenêtre privée : la même amende doit apparaître.
Modifier son statut et vérifier le Sheet. Supprimer l'amende test via l'admin après validation.
Les paiements Wero restent à vérifier et à saisir manuellement dans l'admin.

## Mises à jour
Après modification de `Code.gs`, utiliser **Déployer → Gérer les déploiements → Modifier → Nouvelle version** en conservant l'URL.
Ne pas ouvrir l'URL dans un navigateur pour tester : l'API attend un POST authentifié du serveur Streamlit.

