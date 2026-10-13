"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {RECORDS, lookup, parseCSV, batchRows, escapeCSV} = require("../web/app.js");

test("catalog lookup", () => {
  assert.equal(RECORDS.length, 25);
  assert.equal(lookup("ketoconazole")[0].role, "inhibitor");
  assert.equal(lookup("fluoxetine")[0].enzyme, "CYP2D6");
  assert.equal(lookup("notadrug").length, 0);
  assert.equal(lookup("inhibitor").length, 5);
  assert.deepEqual(lookup(""), []);
});
test("quoted CSV", () => {
  const rows = parseCSV('\uFEFFdrug,notes\r\n"warfarin","line1\nline2 ""quoted"", ok"\r\n');
  assert.deepEqual(rows, [["drug","notes"],["warfarin",'line1\nline2 "quoted", ok']]);
});
test("batch and formula neutralization", () => {
  const result = batchRows('query,notes\nketoconazole,=2+3\nwarfarin,"plain, note"\n');
  assert.equal(result.count, 2);
  assert.equal(result.rows[0][2], "Ketoconazole - strong CYP3A4 inhibitor");
  assert.ok(result.csv.includes('"\'=2+3"'));
  assert.equal(escapeCSV("@SUM(1,1)"), '"\'@SUM(1,1)"');
});
test("invalid rows rejected", () => {
  assert.throws(() => batchRows('drug\n"unclosed'), /Unclosed/);
  assert.throws(() => batchRows('drug,name\nwarfarin'), /row 2/);
  assert.throws(() => batchRows('drug,DRUG\nx,y'), /unique/);
});
