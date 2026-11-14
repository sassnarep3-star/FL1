/* FL1 — small progressive-enhancement helpers.
   The site is fully readable without this file: every table is rendered on the
   server side at authoring time. This only adds convenience. */

(function () {
  "use strict";

  /* ---- 1. filter box for large tables -------------------------------- */
  var tables = document.querySelectorAll("table.searchable");
  if (tables.length) {
    Array.prototype.forEach.call(tables, function (tbl) {
      var wrap = tbl.closest(".twrap") || tbl.parentNode;
      var input = document.createElement("input");
      input.type = "search";
      input.className = "filter";
      input.placeholder = "Filter rows — team, player, position\u2026";
      input.setAttribute("aria-label", "Filter table rows");
      input.addEventListener("input", function () {
        var q = input.value.trim().toLowerCase();
        var rows = tbl.tBodies[0].rows;
        var shown = 0;
        for (var i = 0; i < rows.length; i++) {
          var hit = q === "" || rows[i].textContent.toLowerCase().indexOf(q) !== -1;
          rows[i].style.display = hit ? "" : "none";
          if (hit) shown++;
        }
        var note = wrap.querySelector(".filter-count");
        if (!note) {
          note = document.createElement("p");
          note.className = "filter-count muted";
          wrap.insertBefore(note, wrap.firstChild);
        }
        note.textContent = q === ""
          ? ""
          : shown + " of " + rows.length + " rows match \u201c" + input.value + "\u201d";
      });
      wrap.insertBefore(input, wrap.firstChild);
    });
  }

  /* ---- 2. highlight the row a #fragment points at -------------------- */
  function mark() {
    var id = (location.hash || "").slice(1);
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    var box = el.closest("section, tr, div");
    if (!box) return;
    box.style.transition = "background-color .4s";
    box.style.backgroundColor = "#fff8e1";
    setTimeout(function () { box.style.backgroundColor = ""; }, 1800);
  }
  window.addEventListener("hashchange", mark);
  mark();

  /* ---- 3. mark external links for clarity ---------------------------- */
  Array.prototype.forEach.call(document.querySelectorAll('a[target="_blank"]'), function (a) {
    if (!/[\u2197]$/.test(a.textContent)) {
      a.setAttribute("rel", "noopener noreferrer");
    }
  });
})();
