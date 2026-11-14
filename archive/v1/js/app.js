/* FL1 - simple table search helpers (no external dependencies) */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('table[data-search]').forEach(function (table) {
    var input = document.getElementById(table.dataset.search);
    if (!input) return;
    input.addEventListener('input', function () {
      var term = input.value.toLowerCase();
      var rows = table.querySelectorAll('tbody tr');
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(term) > -1 ? '' : 'none';
      });
    });
  });
});
