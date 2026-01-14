function copyText(id, btn) {
    const el = document.getElementById(id);
    navigator.clipboard.writeText(el.textContent).then(() => showCopied(btn));
}
function copyThis(btn) {
    const text = btn.parentElement.querySelector('span').textContent;
    navigator.clipboard.writeText(text).then(() => showCopied(btn));
}
function copyPostOnly(btn) {
    const body = document.getElementById('postBody').cloneNode(true);
    const prev = body.querySelector('.previously');
    if (prev) prev.remove();
    navigator.clipboard.writeText(body.innerHTML).then(() => showCopied(btn));
}
function copyPreviouslyOnly(btn) {
    const prev = document.getElementById('previously');
    const html = '<p><strong>Previously:</strong><br>' +
        Array.from(prev.querySelectorAll('li')).map(li => '• ' + li.innerHTML).join('<br>') + '</p>';
    navigator.clipboard.writeText(html).then(() => showCopied(btn));
}
function showCopied(btn) {
    const original = btn.textContent;
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = original; btn.classList.remove('copied'); }, 2000);
}
