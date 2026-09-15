// Phénix Bank : coller dans Extensions > Apps Script du classeur.
// Définir SPREADSHEET_ID et API_KEY dans les propriétés du script.
const TABLES = {players:"Joueurs", rules:"Règles", fines:"Amendes", payments:"Paiements"};
const HEADERS = {
  "players": {
    "id": "Identifiant",
    "first_name": "Prénom",
    "last_name": "Nom",
    "jersey_number": "Numéro",
    "photo_path": "Photo",
    "position": "Poste",
    "active": "Actif"
  },
  "rules": {
    "id": "Identifiant",
    "label_fr": "Motif (FR)",
    "label_hu": "Motif (HU)",
    "amount": "Montant (€)",
    "active": "Actif"
  },
  "fines": {
    "id": "Identifiant",
    "player_id": "Joueur (ID)",
    "rule_id": "Règle (ID)",
    "custom_reason": "Motif personnalisé",
    "base_amount": "Montant de base (€)",
    "final_amount": "Montant final (€)",
    "match_day": "Jour de match",
    "status": "Statut",
    "fine_date": "Date",
    "comment": "Commentaire"
  },
  "payments": {
    "id": "Identifiant",
    "player_id": "Joueur (ID)",
    "amount": "Montant (€)",
    "payment_date": "Date",
    "method": "Méthode",
    "comment": "Commentaire"
  }
};

function doPost(e) {
  let lock;
  try {
    const request = JSON.parse(e.postData.contents);
    const properties = PropertiesService.getScriptProperties();
    const key = properties.getProperty("API_KEY");
    if (!key || key.length < 32 || request.api_key !== key) throw new Error("Accès refusé.");
    if (!["read","insert","update","delete"].includes(request.action)) throw new Error("Action invalide.");
    // Un verrou protège les lectures et les écritures concurrentes.
    lock = LockService.getScriptLock();
    lock.waitLock(20000);
    const book = SpreadsheetApp.openById(properties.getProperty("SPREADSHEET_ID"));
    if (request.action === "read") {
      const data = {};
      Object.keys(TABLES).forEach(table => { data[table] = readTable_(book, table); });
      return json_({ok:true, data:data});
    }
    const table = request.table;
    if (!Object.prototype.hasOwnProperty.call(TABLES, table)) throw new Error("Table invalide.");
    const sheet = book.getSheetByName(TABLES[table]);
    const headers = validateHeaders_(sheet, table);
    const fields = HEADERS[table];
    const payload = request.payload || {};
    if (typeof payload !== "object" || Array.isArray(payload)) throw new Error("Données invalides.");
    Object.keys(payload).forEach(field => {
      if (field === "id" || !Object.prototype.hasOwnProperty.call(fields,field)) throw new Error("Champ invalide.");
      const value = payload[field];
      if (value !== null && !["string","number","boolean"].includes(typeof value)) throw new Error("Valeur invalide.");
      if (typeof value === "string" && value.length > 5000) throw new Error("Texte trop long.");
    });
    if (request.action === "insert") {
      const row = Object.assign({id:Utilities.getUuid()}, payload);
      const reverse = {};
      Object.keys(fields).forEach(field => { reverse[fields[field]] = field; });
      sheet.appendRow(headers.map(label => safeCell_(row[reverse[label]])));
      SpreadsheetApp.flush();
      return json_({ok:true, data:row});
    }
    const ids = sheet.getLastRow() > 1
      ? sheet.getRange(2,headers.indexOf(fields.id)+1,sheet.getLastRow()-1,1).getValues() : [];
    const index = ids.findIndex(row => String(row[0]) === String(request.row_id));
    if (index < 0) throw new Error("Ligne introuvable.");
    const rowNumber = index + 2;
    if (request.action === "delete") sheet.deleteRow(rowNumber);
    else {
      const range = sheet.getRange(rowNumber,1,1,headers.length);
      const values = range.getValues()[0];
      Object.keys(payload).forEach(field => { values[headers.indexOf(fields[field])] = safeCell_(payload[field]); });
      range.setValues([values]);
    }
    SpreadsheetApp.flush();
    return json_({ok:true, data:null});
  } catch (error) {
    // Ne pas renvoyer de détails de compte ou de secrets.
    return json_({ok:false, error:"Requête refusée ou configuration du classeur invalide."});
  } finally {
    if (lock && lock.hasLock()) lock.releaseLock();
  }
}

function validateHeaders_(sheet, table) {
  if (!sheet) throw new Error("Onglet manquant.");
  const headers = sheet.getRange(1,1,1,sheet.getLastColumn()).getValues()[0];
  Object.values(HEADERS[table]).forEach(label => {
    if (headers.filter(header => header === label).length !== 1) throw new Error("Colonne invalide.");
  });
  return headers;
}

function readTable_(book, table) {
  const sheet = book.getSheetByName(TABLES[table]);
  const headers = validateHeaders_(sheet, table);
  if (sheet.getLastRow() <= 1) return [];
  const timezone = book.getSpreadsheetTimeZone();
  return sheet.getRange(2,1,sheet.getLastRow()-1,headers.length).getValues()
    .filter(values => values[headers.indexOf(HEADERS[table].id)] !== "")
    .map(values => {
      const row = {};
      Object.keys(HEADERS[table]).forEach(field => {
        const value = values[headers.indexOf(HEADERS[table][field])];
        row[field] = value instanceof Date ? Utilities.formatDate(value,timezone,"yyyy-MM-dd") : value;
      });
      return row;
    });
}

function safeCell_(value) {
  if (value === undefined || value === null) return "";
  // Empêcher les textes saisis dans l'app de devenir des formules Sheets.
  return typeof value === "string" && /^[=+@-]/.test(value) ? "'" + value : value;
}

function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}

