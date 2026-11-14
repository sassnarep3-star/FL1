// FL1 — Site behavior: table sorting, filtering, status badges
(function () {
  'use strict';

  // Escape HTML to prevent injection from data
  function esc(t) {
    return String(t == null ? '' : t)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Initialize all sortable/filterable tables
  function initTables() {
    document.querySelectorAll('table.sortable').forEach(function (table) {
      var headers = table.querySelectorAll('th');
      headers.forEach(function (th, idx) {
        if (!th.classList.contains('nosort')) return;
        th.style.cursor = 'pointer';
        th.title = 'Click to sort';
        th.addEventListener('click', function () {
          var dir = th.dataset.dir !== 'desc' ? 'asc' : 'desc';
          var tbody = table.querySelector('tbody');
          var rows = Array.from(tbody.querySelectorAll('tr'));
          var colIndex = idx;

          rows.sort(function (a, b) {
            var av = a.children[colIndex] ? a.children[colIndex].textContent.trim() : '';
            var bv = b.children[colIndex] ? b.children[colIndex].textContent.trim() : '';
            // numeric compare
            var an = parseFloat(av.replace(/[^0-9.-]/g, ''));
            var bn = parseFloat(bv.replace(/[^0-9.-]/g, ''));
            if (!isNaN(an) && !isNaN(bn) && av.match(/^[\s\$0-9.,%()-]*$/)) {
              return dir === 'asc' ? an - bn : bn - an;
            }
            return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
          });

          headers.forEach(function (h) { delete h.dataset.dir; h.classList.remove('sorted-asc', 'sorted-desc'); });
          th.dataset.dir = dir;
          th.classList.add(dir === 'asc' ? 'sorted-asc' : 'sorted-desc');
          rows.forEach(function (r) { tbody.appendChild(r); });
        });
      });
    });
  }

  // Filter table rows by a text input whose data-target matches table id
  function initFilters() {
    document.querySelectorAll('[data-filter]').forEach(function (input) {
      var targetId = input.getAttribute('data-filter');
      var table = document.getElementById(targetId);
      if (!table) return;
      var tbody = table.querySelector('tbody');
      var rows = tbody.querySelectorAll('tr');
      var countEl = document.getElementById(targetId + '-count');
      function run() {
        var q = input.value.toLowerCase();
        var shown = 0;
        rows.forEach(function (row) {
          var text = row.textContent.toLowerCase();
          var match = text.indexOf(q) !== -1;
          row.style.display = match ? '' : 'none';
          if (match) shown++;
        });
        if (countEl) countEl.textContent = shown + ' of ' + rows.length + ' rows';
      }
      input.addEventListener('input', run);
      run();
    });
  }

  // Status badge color pills
  function badges() {
    document.querySelectorAll('.status-pill').forEach(function (el) {
      var v = el.textContent.toLowerCase();
      el.classList.remove('status-out', 'status-questionable', 'status-doubtful');
      if (v === 'out') el.classList.add('status-out');
      else if (v === 'questionable') el.classList.add('status-questionable');
      else if (v === 'doubtful') el.classList.add('status-doubtful');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTables();
    initFilters();
    badges();
  });
})();
