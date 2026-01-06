function copyText(id) {
    const el = document.getElementById(id);
    navigator.clipboard.writeText(el.textContent).then(() => showCopied(event.target));
}
function copyThis(btn) {
    const text = btn.parentElement.querySelector('span').textContent;
    navigator.clipboard.writeText(text).then(() => showCopied(btn));
}
function copyBodyAndPreviously() {
    navigator.clipboard.writeText(document.getElementById('postBody').innerHTML).then(() => showCopied(event.target));
}
function copyPreviouslyOnly() {
    const prev = document.getElementById('previously');
    const html = '<p><strong>Previously:</strong><br>' +
        Array.from(prev.querySelectorAll('li')).map(li => '• ' + li.innerHTML).join('<br>') + '</p>';
    navigator.clipboard.writeText(html).then(() => showCopied(event.target));
}
function showCopied(btn) {
    const original = btn.textContent;
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = original; btn.classList.remove('copied'); }, 1500);
}
