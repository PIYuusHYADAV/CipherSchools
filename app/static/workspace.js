// Dynamic class/relationship builder. No framework, kept intentionally simple.

let classRowCount = 0;
let relRowCount = 0;

function addClassRow(data) {
  data = data || { name: "", kind: "class", fields: [], methods: [] };
  const id = classRowCount++;
  const container = document.getElementById("classes-container");
  const row = document.createElement("div");
  row.className = "row-card";
  row.id = `class-row-${id}`;
  row.innerHTML = `
    <div class="row-fields">
      <input type="text" placeholder="Class name (e.g. ParkingSpot)" class="class-name" value="${escapeHtml(data.name)}">
      <select class="class-kind">
        <option value="class" ${data.kind === "class" ? "selected" : ""}>class</option>
        <option value="interface" ${data.kind === "interface" ? "selected" : ""}>interface</option>
      </select>
      <button type="button" class="btn btn-danger btn-small" onclick="removeRow('class-row-${id}')">Remove</button>
    </div>
    <input type="text" placeholder="Fields, comma-separated (e.g. spotId, isOccupied)" class="class-fields" value="${escapeHtml((data.fields || []).join(', '))}">
    <input type="text" placeholder="Methods, comma-separated (e.g. occupy(), release())" class="class-methods" value="${escapeHtml((data.methods || []).join(', '))}">
  `;
  container.appendChild(row);
}

function addRelationshipRow(data) {
  data = data || { source: "", target: "", kind: "association" };
  const id = relRowCount++;
  const container = document.getElementById("relationships-container");
  const row = document.createElement("div");
  row.className = "row-card";
  row.id = `rel-row-${id}`;
  row.innerHTML = `
    <div class="row-fields">
      <input type="text" placeholder="Source class" class="rel-source" value="${escapeHtml(data.source)}">
      <select class="rel-kind">
        <option value="association" ${data.kind === "association" ? "selected" : ""}>uses / association</option>
        <option value="composition" ${data.kind === "composition" ? "selected" : ""}>has-a / composition</option>
        <option value="inheritance" ${data.kind === "inheritance" ? "selected" : ""}>inherits from</option>
        <option value="implements" ${data.kind === "implements" ? "selected" : ""}>implements</option>
      </select>
      <input type="text" placeholder="Target class" class="rel-target" value="${escapeHtml(data.target)}">
      <button type="button" class="btn btn-danger btn-small" onclick="removeRow('rel-row-${id}')">Remove</button>
    </div>
  `;
  container.appendChild(row);
}

function removeRow(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function escapeHtml(str) {
  return (str || "").replace(/[&<>"']/g, (m) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[m]));
}

function serializeBeforeSubmit() {
  const classes = [];
  document.querySelectorAll("#classes-container .row-card").forEach((row) => {
    const name = row.querySelector(".class-name").value.trim();
    if (!name) return; // skip empty rows
    const kind = row.querySelector(".class-kind").value;
    const fields = row.querySelector(".class-fields").value.split(",").map(s => s.trim()).filter(Boolean);
    const methods = row.querySelector(".class-methods").value.split(",").map(s => s.trim()).filter(Boolean);
    classes.push({ name, kind, fields, methods });
  });

  const relationships = [];
  document.querySelectorAll("#relationships-container .row-card").forEach((row) => {
    const source = row.querySelector(".rel-source").value.trim();
    const target = row.querySelector(".rel-target").value.trim();
    if (!source || !target) return;
    const kind = row.querySelector(".rel-kind").value;
    relationships.push({ source, target, kind });
  });

  document.getElementById("classes_json").value = JSON.stringify(classes);
  document.getElementById("relationships_json").value = JSON.stringify(relationships);
  return true;
}

// Pre-populate from any previously saved draft, or start with one empty class row.
if (initialClasses && initialClasses.length > 0) {
  initialClasses.forEach(addClassRow);
} else {
  addClassRow();
}
if (initialRelationships && initialRelationships.length > 0) {
  initialRelationships.forEach(addRelationshipRow);
}
