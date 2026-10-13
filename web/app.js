"use strict";

/* This is a local, educational CYP-role catalog, not a clinical DDI rules engine. */
const RECORDS = [
  ["Ketoconazole", "CYP3A4", "inhibitor", "major", "strong"],
  ["Itraconazole", "CYP3A4", "inhibitor", "major", "strong"],
  ["Clarithromycin", "CYP3A4", "inhibitor", "major", "strong"],
  ["Ritonavir", "CYP3A4", "inhibitor", "major", "strong"],
  ["Simvastatin", "CYP3A4", "substrate", "major", ""],
  ["Midazolam", "CYP3A4", "substrate", "moderate", ""],
  ["Cyclosporine", "CYP3A4", "substrate", "major", ""],
  ["Carbamazepine", "CYP3A4", "inducer", "major", ""],
  ["Phenytoin", "CYP3A4", "inducer", "major", ""],
  ["Rifampin", "CYP3A4", "inducer", "major", ""],
  ["St. John's Wort", "CYP3A4", "inducer", "major", ""],
  ["Fluoxetine", "CYP2D6", "inhibitor", "major", "strong"],
  ["Paroxetine", "CYP2D6", "inhibitor", "major", "strong"],
  ["Quinidine", "CYP2D6", "inhibitor", "major", "strong"],
  ["Codeine", "CYP2D6", "substrate", "major", "prodrug"],
  ["Tamoxifen", "CYP2D6", "substrate", "major", "prodrug"],
  ["Metoprolol", "CYP2D6", "substrate", "moderate", ""],
  ["Omeprazole", "CYP2C19", "inhibitor", "moderate", ""],
  ["Clopidogrel", "CYP2C19", "substrate", "major", "prodrug"],
  ["Warfarin", "CYP2C9", "substrate", "major", ""],
  ["Fluconazole", "CYP2C9", "inhibitor", "moderate", ""],
  ["Fluvoxamine", "CYP1A2", "inhibitor", "major", "strong"],
  ["Caffeine", "CYP1A2", "substrate", "minor", ""],
  ["Efavirenz", "CYP2B6", "substrate", "moderate", ""],
  ["Bupropion", "CYP2B6", "substrate", "moderate", ""]
].map(function (r) {
  const label = r[0] + " - " + (r[4] === "strong" ? "strong " : "") +
    r[1] + " " + r[2] + (r[4] === "prodrug" ? " (prodrug)" : "");
  return {name:r[0], enzyme:r[1], role:r[2], tier:r[3], key:r[0] === "St. John's Wort" ? "st. john" : r[0].toLowerCase(), label:label};
});
const WEIGHTS = {major:3, moderate:2, minor:1};

function lookup(query) {
  const q = String(query == null ? "" : query).trim().toLowerCase();
  if (!q) return [];
  const qt = new Set(q.split(/\s+/));
  return RECORDS.map(function (r, index) {
    const terms = new Set(r.label.toLowerCase().split(/\s+/));
    let score = r.key && q.includes(r.key) ? 10 : 0;
    qt.forEach(function (term) { if (terms.has(term)) score += 2; });
    if (!score) return null;
    return {name:r.name, enzyme:r.enzyme, role:r.role, tier:r.tier,
      label:r.label, score:score + WEIGHTS[r.tier], index:index};
  }).filter(Boolean).sort(function (a,b) {
    return b.score - a.score || a.index - b.index;
  }).slice(0, 5);
}

/* RFC 4180-style quoting, including quoted commas, newlines and "" escapes. */
function parseCSV(text) {
  if (typeof text !== "string") throw new Error("CSV input must be text.");
  const rows = [];
  let row = [], field = "", quoted = false, afterQuote = false;
  text = text.replace(/^\uFEFF/, "");
  for (let i=0; i<text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i+1] === '"') { field += '"'; i++; }
        else { quoted = false; afterQuote = true; }
      } else { field += c; }
    } else if (afterQuote) {
      if (c === ',') { row.push(field); field=""; afterQuote=false; }
      else if (c === '\r' || c === '\n') {
        if (c === '\r' && text[i+1] === '\n') i++;
        row.push(field); rows.push(row); row=[]; field=""; afterQuote=false;
      } else if (c !== ' ' && c !== '\t') { throw new Error("Unexpected character after closing quote."); }
    } else if (c === '"' && field === "") { quoted=true; }
    else if (c === ',') { row.push(field); field=""; }
    else if (c === '\r' || c === '\n') {
      if (c === '\r' && text[i+1] === '\n') i++;
      row.push(field); rows.push(row); row=[]; field="";
    } else if (c === '"') { throw new Error("Unexpected quote in unquoted field."); }
    else { field += c; }
  }
  if (quoted) throw new Error("Unclosed quoted CSV field.");
  if (afterQuote || field !== "" || row.length) { row.push(field); rows.push(row); }
  return rows;
}
function escapeCSV(value) {
  let s = String(value == null ? "" : value);
  /* Prevent spreadsheet formula evaluation, including leading whitespace. */
  if (/^\s*[=+\-@]/.test(s) || /^[\t\r]/.test(s)) s = "'" + s;
  return '"' + s.replace(/"/g, '""') + '"';
}
function batchRows(csvText) {
  const rows = parseCSV(csvText);
  if (!rows.length || !rows[0].length || rows[0].every(function (h) { return !h.trim(); }))
    throw new Error("The CSV has no header row.");
  const header = rows[0].map(function (v) { return v.trim(); });
  if (header.some(function (v) { return !v; })) throw new Error("CSV contains a blank column heading.");
  if (new Set(header.map(function (v) {return v.toLowerCase();})).size !== header.length)
    throw new Error("CSV headers must be unique (case-insensitive).");
  const preferences = ["query","test","drug","code","variant","hla","lab","name"];
  const column = preferences.map(function (p) {
    return header.findIndex(function (h) {return h.toLowerCase() === p;});
  }).find(function (v) {return v >= 0;});
  const columnIndex = column === undefined ? 0 : column;
  const output = [];
  for (let i=1; i<rows.length; i++) {
    const row = rows[i];
    if (row.length === 1 && !row[0].trim()) continue;
    if (row.length !== header.length) throw new Error("CSV row " + (i+1) + " has " + row.length + " columns, expected " + header.length + ".");
    const matches = lookup(row[columnIndex]);
    const top = matches[0];
    output.push(row.concat([top ? top.label : "no match", top ? top.score : 0,
      top ? top.role : "", top ? top.tier : ""]));
    if (output.length > 5000) throw new Error("Limit: 5,000 data rows per file.");
  }
  const columns = header.concat(["top_hit","lookup_score","interaction_type","severity"]);
  return {columns:columns, rows:output, count:output.length,
    csv:[columns].concat(output).map(function (r) {return r.map(escapeCSV).join(",");}).join("\r\n") + "\r\n"};
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = {RECORDS, lookup, parseCSV, escapeCSV, batchRows};
}

if (typeof document !== "undefined") {
  const $ = function (id) {return document.getElementById(id);};
  const results = $("results");
  const search = $("drugQuery");
  const status = $("status");
  function addElement(parent, tag, text, className) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text;
    parent.appendChild(el);
    return el;
  }
  function showResults() {
    results.replaceChildren();
    const query = search.value.trim();
    if (!query) { addElement(results, "p", "Enter a drug or CYP search term.", "empty"); return; }
    const matches = lookup(query);
    if (!matches.length) {
      addElement(results, "p", "No catalog match. This does not rule out interactions.", "empty");
      return;
    }
    matches.forEach(function (m) {
      const card = addElement(results, "article", "", "hit");
      const heading = addElement(card, "div", "", "hit-head");
      addElement(heading, "strong", m.name);
      addElement(heading, "span", m.enzyme, "enzyme");
      addElement(card, "p", "Role: " + m.role + " · Legacy catalog tier: " + m.tier);
      addElement(card, "small", "Search relevance score: " + m.score + " (not a clinical risk score)");
    });
  }
  $("searchForm").addEventListener("submit", function (e) {e.preventDefault(); showResults();});
  $("example").addEventListener("click", function () { search.value="ketoconazole"; showResults(); search.focus(); });
  $("recordCount").textContent = String(RECORDS.length);
  $("csvFile").addEventListener("change", async function (e) {
    const file = e.target.files[0];
    $("download").hidden = true;
    $("preview").replaceChildren();
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { status.textContent="File is larger than 2 MB."; return; }
    try {
      const output = batchRows(await file.text());
      status.textContent = output.count + " row(s) processed locally. No data was uploaded.";
      const table = document.createElement("table");
      const thead = document.createElement("thead"), tr = document.createElement("tr");
      output.columns.forEach(function (h) {addElement(tr,"th",h);});
      thead.appendChild(tr); table.appendChild(thead);
      const tbody = document.createElement("tbody");
      output.rows.slice(0, 8).forEach(function (r) {
        const rEl = document.createElement("tr");
        r.forEach(function (v) {addElement(rEl,"td",String(v));});
        tbody.appendChild(rEl);
      });
      table.appendChild(tbody); $("preview").appendChild(table);
      if (output.count > 8) addElement($("preview"),"p","Preview shows the first 8 rows.","caption");
      $("download").hidden=false;
      $("download").onclick=function () {
        const blob = new Blob([output.csv], {type:"text/csv;charset=utf-8"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href=url; a.download="cyp_lookup_results.csv"; document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      };
    } catch(err) {status.textContent="Could not process CSV: " + err.message;}
  });
  showResults();
}