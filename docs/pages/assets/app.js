
// Table filter: one input per large table, no dependencies, harmless if JS is disabled.
document.addEventListener('input', function (e) {
  var box = e.target.closest('[data-filter]');
  if (!box) return;
  var q = box.value.trim().toLowerCase();
  document.querySelectorAll(box.getAttribute('data-filter') + ' tbody tr').forEach(function (tr) {
    tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) > -1) ? '' : 'none';
  });
});
