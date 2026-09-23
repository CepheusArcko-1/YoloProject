'use strict';

// ---------- Outils ----------
const $ = id => document.getElementById(id);
const LABELS = window.LABELS || {};
const IMAGE_NAME = /\.(jpe?g|png|bmp|webp)$/i;
const dateFormat = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });

const label = name => {
    const fr = LABELS[name] || name;
    return fr.charAt(0).toUpperCase() + fr.slice(1);
};
const escapeHtml = text => String(text).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const formatDate = iso => dateFormat.format(new Date(iso));
const plural = (n, one, many) => `${n} ${n > 1 ? many : one}`;
const seconds = ms => `${(ms / 1000).toFixed(2).replace('.', ',')} s`;
const stem = name => name.replace(/\.[^.]+$/, '');
const resultUrl = (id, file) => `/results/${id}/${encodeURIComponent(file)}`;
// Texte sombre sur les couleurs claires, blanc sinon
const textColor = hex => {
    const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
    return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#141414' : '#fff';
};
const TRASH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/></svg>';

function toast(message, isError = false) {
    const el = $('toast');
    el.textContent = message;
    el.classList.toggle('error', isError);
    el.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.hidden = true, 4000);
}

async function getJson(url, options) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Une erreur est survenue.');
    return data;
}

// ---------- Vues ----------
function show(name) {
    for (const view of ['home', 'single', 'batch']) $(`view-${view}`).hidden = view !== name;
}

let busy = false;   // une analyse (simple ou par lot) est en cours

// ---------- Modèle et matériel ----------
let settings = null;

function renderModels() {
    $('models').innerHTML = settings.models.map(m => {
        const active = m.id === settings.model;
        const title = m.description + (m.downloaded ? '' : ' — téléchargé à la première sélection');
        return `<button type="button" role="radio" aria-checked="${active}" class="${active ? 'active' : ''}"
                        data-model="${m.id}" title="${escapeHtml(title)}">${escapeHtml(m.label)}</button>`;
    }).join('');
    $('device').querySelector('span').textContent = settings.device;
}

$('models').addEventListener('click', async e => {
    const button = e.target.closest('[data-model]');
    if (!button || button.classList.contains('active')) return;
    const model = settings.models.find(m => m.id === button.dataset.model);
    $('models').querySelectorAll('button').forEach(b => b.disabled = true);
    button.innerHTML = `<span class="spinner mini-spinner"></span>${escapeHtml(model.label)}`;
    if (!model.downloaded) toast(`Téléchargement du modèle « ${model.label} »…`);
    try {
        settings = await getJson('/settings', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: model.id }),
        });
        toast(`Modèle « ${model.label} » utilisé pour les prochaines analyses.`);
    } catch (err) {
        toast(err.message === 'Failed to fetch' ? 'Impossible de charger ce modèle.' : err.message, true);
    } finally {
        renderModels();
    }
});

// ---------- Historique ----------
let historyItems = [];

const classesText = item => item.count
    ? item.classes.slice(0, 3).map(([name, n]) => `${label(name)} ${n}`).join(', ')
      + (item.classes.length > 3 ? '…' : '')
    : 'Aucun objet';

const cardHtml = item => `
    <button class="thumb-card" type="button" data-open="${item.id}">
        <img src="${resultUrl(item.id, 'thumbnail.jpg')}" alt="" loading="lazy">
        <div class="body">
            <div class="name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="sub">${plural(item.count, 'objet', 'objets')} · ${formatDate(item.created)}</div>
        </div>
    </button>`;

async function refreshHistory() {
    try {
        historyItems = await getJson('/history');
    } catch {
        return;
    }
    $('recent').hidden = !historyItems.length;
    $('recent-cards').innerHTML = historyItems.slice(0, 8).map(cardHtml).join('');

    $('history-count').textContent = historyItems.length ? `(${historyItems.length})` : '';
    $('history-list').innerHTML = historyItems.map(item => `
        <li class="history-item" data-open="${item.id}">
            <img src="${resultUrl(item.id, 'thumbnail.jpg')}" alt="" loading="lazy">
            <div style="min-width:0">
                <div class="name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
                <div class="sub">${formatDate(item.created)} · ${escapeHtml(item.model_label)}</div>
                <div class="sub">${escapeHtml(classesText(item))}</div>
            </div>
            <button class="btn btn-danger-ghost btn-icon" type="button" data-delete="${item.id}" title="Supprimer">${TRASH_ICON}</button>
        </li>`).join('') || '<li class="empty">Aucune analyse pour le moment.</li>';
    $('history-csv').hidden = !historyItems.length;
    $('history-csv').href = `/export.csv?ids=${historyItems.map(i => i.id).join(',')}`;
}

function openHistory() {
    $('history').hidden = $('history-backdrop').hidden = false;
    refreshHistory();
}
function closeHistory() {
    $('history').hidden = $('history-backdrop').hidden = true;
}
$('history-open').addEventListener('click', openHistory);
$('history-close').addEventListener('click', closeHistory);
$('history-backdrop').addEventListener('click', closeHistory);

// Suppression en deux clics, pour éviter les erreurs
async function deleteAnalysis(button, id) {
    if (!button.classList.contains('confirm')) {
        button.classList.add('confirm');
        toast('Cliquez à nouveau pour supprimer cette analyse.');
        setTimeout(() => button.classList.remove('confirm'), 3000);
        return;
    }
    try {
        await getJson(`/history/${id}`, { method: 'DELETE' });
    } catch (err) {
        return toast(err.message, true);
    }
    toast('Analyse supprimée.');
    if (batch) {
        batch.items.forEach(item => { if (item.record && item.record.id === id) item.status = 'deleted'; });
        renderBatch();
    }
    if (current && current.id === id) {
        current = null;
        show(batch ? 'batch' : 'home');
    }
    refreshHistory();
}

// Un seul écouteur pour tous les éléments « ouvrir » et « supprimer » créés dynamiquement
document.addEventListener('click', e => {
    const del = e.target.closest('[data-delete]');
    if (del) {
        e.stopPropagation();
        return deleteAnalysis(del, del.dataset.delete);
    }
    const open = e.target.closest('[data-open]');
    if (open) return openAnalysis(open.dataset.open, !!open.closest('#batch-cards'));
    if (e.target.closest('[data-open-history]')) openHistory();
});

// ---------- Une analyse ----------
const frame = $('frame');
const image = $('image');
const boxes = $('boxes');
let current = null;

function resetPanel() {
    boxes.innerHTML = '';
    $('count').textContent = '0';
    $('chips').innerHTML = $('list').innerHTML = '';
    $('meta').textContent = $('duration').textContent = '';
}

async function postImage(file) {
    const data = new FormData();
    data.append('image', file, file.name);
    try {
        return await getJson('/detect', { method: 'POST', body: data });
    } catch (err) {
        throw new Error(err.message === 'Failed to fetch' ? 'Erreur pendant l\'analyse.' : err.message);
    }
}

async function analyzeOne(file) {
    busy = true;
    batch = null;
    current = null;
    show('single');
    $('back').hidden = true;
    resetPanel();
    $('filename').textContent = file.name;
    $('overlay').hidden = false;
    image.onload = null;
    image.src = URL.createObjectURL(file);
    try {
        renderRecord(await postImage(file), true);
        refreshHistory();
    } catch (err) {
        toast(err.message, true);
        show('home');
    } finally {
        $('overlay').hidden = true;
        busy = false;
    }
}

async function openAnalysis(id, fromBatch = false) {
    closeHistory();
    let record;
    try {
        record = await getJson(`/history/${id}`);
    } catch (err) {
        toast(err.message, true);
        return refreshHistory();
    }
    show('single');
    $('back').hidden = !(fromBatch && batch);
    resetPanel();
    renderRecord(record, false);
}

function renderRecord(record, keepImage) {
    current = record;
    $('filename').textContent = record.name;
    $('meta').textContent = `${formatDate(record.created)} · Modèle ${record.model_label}`;
    $('duration').textContent = record.duration_ms != null
        ? `Analysé en ${seconds(record.duration_ms)}${record.device ? ` · ${record.device}` : ''}` : '';
    $('download').href = resultUrl(record.id, 'annotated.jpg');
    $('download').download = `${stem(record.name)}_annote.jpg`;
    $('json').href = resultUrl(record.id, 'analysis.json');
    $('json').download = `${stem(record.name)}.json`;
    $('csv').href = `/export.csv?ids=${record.id}`;
    $('delete').dataset.delete = record.id;
    image.onload = update;
    if (!keepImage) image.src = resultUrl(record.id, record.original);
    else if (image.complete && image.naturalWidth) update();
}

function update() {
    if (!current) return;
    const min = Number($('threshold').value) / 100;
    $('threshold-value').textContent = `${$('threshold').value}%`;
    const visible = current.detections
        .map((d, i) => ({ ...d, i }))
        .filter(d => d.confidence >= min)
        .sort((a, b) => b.confidence - a.confidence);

    $('count').textContent = visible.length;
    $('count-label').textContent = visible.length > 1 ? 'objets détectés' : 'objet détecté';

    const groups = {};
    visible.forEach(d => (groups[d.class] ??= { color: d.color, n: 0 }).n++);
    $('chips').innerHTML = Object.entries(groups)
        .sort((a, b) => b[1].n - a[1].n)
        .map(([name, g]) => `<span class="chip"><span class="dot" style="background:${g.color}"></span>${escapeHtml(label(name))} <b>${g.n}</b></span>`)
        .join('') || '<span class="empty">Aucun objet</span>';

    $('list').innerHTML = visible.map(d => `
        <li class="item" data-i="${d.i}">
            <span class="dot" style="background:${d.color}"></span>
            <span class="name">${escapeHtml(label(d.class))}</span>
            <span class="pct">${Math.round(d.confidence * 100)}%</span>
            <span class="bar"><i style="width:${d.confidence * 100}%;background:${d.color}"></i></span>
        </li>`).join('') || '<li class="empty">Aucun objet au-dessus de ce seuil.</li>';

    // Cadres dessinés par-dessus l'image, à l'échelle de l'image d'origine
    const w = image.naturalWidth, h = image.naturalHeight;
    const scale = w / image.clientWidth || 1;
    const font = 13 * scale, pad = 5 * scale;
    boxes.setAttribute('viewBox', `0 0 ${w} ${h}`);
    boxes.innerHTML = visible.slice().reverse().map(d => {
        const [x1, y1, x2, y2] = d.bounding_box;
        const text = `${label(d.class)} ${Math.round(d.confidence * 100)}%`;
        const tw = text.length * font * 0.58 + pad * 2, th = font + pad * 1.6;
        const ty = y1 - th < 0 ? y1 : y1 - th;
        return `<g class="box" data-i="${d.i}">
            <rect class="fill" x="${x1}" y="${y1}" width="${x2 - x1}" height="${y2 - y1}" fill="${d.color}"/>
            <rect class="outline" x="${x1}" y="${y1}" width="${x2 - x1}" height="${y2 - y1}" rx="${3 * scale}" stroke="${d.color}"/>
            <rect x="${x1}" y="${ty}" width="${tw}" height="${th}" rx="${3 * scale}" fill="${d.color}"/>
            <text class="box-label" x="${x1 + pad}" y="${ty + th - pad * 1.1}" fill="${textColor(d.color)}" style="font-size:${font}px">${escapeHtml(text)}</text>
        </g>`;
    }).join('');
}

// Survol : met en évidence le cadre et la ligne correspondants
function highlight(i) {
    frame.classList.toggle('focus', i != null);
    document.querySelectorAll('#list [data-i], #boxes [data-i]')
        .forEach(el => el.classList.toggle('active', el.dataset.i === i));
}
for (const el of [$('list'), boxes]) {
    el.addEventListener('mouseover', e => {
        const target = e.target.closest('[data-i]');
        highlight(target ? target.dataset.i : null);
    });
    el.addEventListener('mouseleave', () => highlight(null));
}
$('threshold').addEventListener('input', update);
window.addEventListener('resize', update);
$('back').addEventListener('click', () => { show('batch'); renderBatch(); });

// ---------- Plusieurs images ----------
let batch = null;

async function analyzeMany(files) {
    busy = true;
    batch = { items: files.map(file => ({ file, status: 'pending', preview: URL.createObjectURL(file) })), running: true, cancelled: false };
    show('batch');
    renderBatch();
    for (const item of batch.items) {
        if (batch.cancelled) {
            item.status = 'skipped';
            continue;
        }
        item.status = 'running';
        renderBatch();
        try {
            item.record = await postImage(item.file);
            item.status = 'done';
        } catch (err) {
            item.status = 'failed';
            item.error = err.message;
        }
        renderBatch();
    }
    batch.running = false;
    busy = false;
    renderBatch();
    refreshHistory();
}

function renderBatch() {
    if (!batch) return;
    const items = batch.items;
    const done = items.filter(i => i.status === 'done');
    const failed = items.filter(i => i.status === 'failed');
    const finished = items.filter(i => !['pending', 'running'].includes(i.status)).length;
    const objects = done.reduce((sum, i) => sum + i.record.detections.length, 0);

    $('batch-title').textContent = batch.running ? `Analyse de ${items.length} images…`
        : batch.cancelled ? 'Analyse arrêtée' : 'Analyse terminée';
    $('batch-meta').textContent = [
        `${finished} / ${items.length} traitées`,
        plural(objects, 'objet détecté', 'objets détectés'),
        failed.length ? `${failed.length} en échec` : '',
    ].filter(Boolean).join(' · ');
    $('batch-progress').querySelector('i').style.width = `${finished / items.length * 100}%`;
    $('batch-progress').hidden = !batch.running;
    $('batch-cancel').hidden = !batch.running;
    $('batch-new').hidden = batch.running;
    $('batch-csv').hidden = batch.running || !done.length;
    $('batch-csv').href = `/export.csv?ids=${done.map(i => i.record.id).join(',')}`;

    const totals = {};
    done.forEach(i => i.record.detections.forEach(d => (totals[d.class] ??= { color: d.color, n: 0 }).n++));
    $('batch-chips').innerHTML = Object.entries(totals)
        .sort((a, b) => b[1].n - a[1].n)
        .map(([name, g]) => `<span class="chip"><span class="dot" style="background:${g.color}"></span>${escapeHtml(label(name))} <b>${g.n}</b></span>`)
        .join('');

    $('batch-cards').innerHTML = items.filter(i => i.status !== 'deleted').map(item => {
        if (item.status === 'done') {
            const r = item.record;
            return cardHtml({ id: r.id, name: r.name, created: r.created, count: r.detections.length });
        }
        const status = {
            pending: 'En attente',
            running: '<span class="spinner mini-spinner"></span>Analyse…',
            failed: escapeHtml(item.error || 'Échec'),
            skipped: 'Non traitée',
        }[item.status];
        return `<div class="thumb-card ${item.status === 'failed' ? 'failed' : 'pending'}">
            <img src="${item.preview}" alt="">
            <div class="body">
                <div class="name" title="${escapeHtml(item.file.name)}">${escapeHtml(item.file.name)}</div>
                <div class="sub status">${status}</div>
            </div>
        </div>`;
    }).join('');
}

$('batch-cancel').addEventListener('click', () => {
    if (batch) batch.cancelled = true;
    $('batch-cancel').hidden = true;
    toast('Arrêt après l\'image en cours…');
});

// ---------- Choix des fichiers : bouton, dossier, glisser-déposer, coller ----------
function handleFiles(files) {
    if (busy) return toast('Une analyse est déjà en cours.', true);
    const images = [...files].filter(f => IMAGE_NAME.test(f.name))
        .sort((a, b) => a.name.localeCompare(b.name, 'fr', { numeric: true }));
    if (!images.length) return toast('Aucune image trouvée (JPG, PNG, BMP ou WEBP).', true);
    images.length === 1 ? analyzeOne(images[0]) : analyzeMany(images);
}

document.querySelectorAll('[data-pick]').forEach(button =>
    button.addEventListener('click', () => $(button.dataset.pick).click()));
for (const input of [$('file'), $('folder')]) {
    input.addEventListener('change', () => {
        handleFiles(input.files);
        input.value = '';
    });
}

// Parcourt les dossiers déposés (et leurs sous-dossiers)
async function droppedFiles(dataTransfer) {
    const entries = [...dataTransfer.items].map(i => i.webkitGetAsEntry && i.webkitGetAsEntry()).filter(Boolean);
    if (!entries.some(entry => entry.isDirectory)) return [...dataTransfer.files];
    const files = [];
    async function walk(entry) {
        if (entry.isFile) {
            files.push(await new Promise((resolve, reject) => entry.file(resolve, reject)));
        } else if (entry.isDirectory) {
            const reader = entry.createReader();
            let chunk;
            do {
                chunk = await new Promise((resolve, reject) => reader.readEntries(resolve, reject));
                for (const child of chunk) await walk(child);
            } while (chunk.length);
        }
    }
    for (const entry of entries) await walk(entry);
    return files;
}

let dragDepth = 0;
window.addEventListener('dragenter', e => { e.preventDefault(); dragDepth++; document.body.classList.add('dragging'); });
window.addEventListener('dragleave', () => { if (--dragDepth <= 0) { dragDepth = 0; document.body.classList.remove('dragging'); } });
window.addEventListener('dragover', e => e.preventDefault());
window.addEventListener('drop', async e => {
    e.preventDefault();
    dragDepth = 0;
    document.body.classList.remove('dragging');
    handleFiles(await droppedFiles(e.dataTransfer));
});
window.addEventListener('paste', e => {
    const item = [...e.clipboardData.items].find(i => i.type.startsWith('image/'));
    if (!item) return;
    const blob = item.getAsFile();
    handleFiles([new File([blob], `image-collee.${blob.type.split('/')[1] || 'png'}`, { type: blob.type })]);
});

// ---------- Webcam ----------
$('webcam').addEventListener('click', async e => {
    const button = e.currentTarget;
    const text = button.querySelector('.label');
    button.disabled = true;
    text.textContent = 'Webcam ouverte…';
    toast('Appuyez sur « q » ou fermez la fenêtre de la webcam pour l\'arrêter.');
    try {
        await getJson('/start-video', { method: 'POST' });
    } catch (err) {
        toast(err.message, true);
    } finally {
        button.disabled = false;
        text.textContent = 'Webcam';
    }
});

// ---------- Menu et désinstallation ----------
const menuList = $('menu-list');
$('menu-button').addEventListener('click', e => { e.stopPropagation(); menuList.hidden = !menuList.hidden; });
document.addEventListener('click', () => menuList.hidden = true);

const modal = $('uninstall-modal');
const closeModal = () => modal.hidden = true;
$('uninstall-open').addEventListener('click', async () => {
    modal.hidden = false;
    $('uninstall-confirm').disabled = true;
    $('uninstall-list').innerHTML = '<li class="muted">Recherche…</li>';
    try {
        const data = await getJson('/uninstall');
        $('uninstall-list').innerHTML = data.items.length
            ? data.items.map(i => `<li><span>${escapeHtml(i.label)}</span><span class="size">${i.size}</span></li>`).join('')
              + `<li class="total"><span>Total libéré</span><span>${data.total}</span></li>`
            : '<li class="muted">Rien à désinstaller.</li>';
        $('uninstall-confirm').disabled = !data.items.length;
    } catch {
        $('uninstall-list').innerHTML = '<li class="muted">Impossible de lister les éléments.</li>';
    }
});
$('uninstall-cancel').addEventListener('click', closeModal);
modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
$('uninstall-confirm').addEventListener('click', async () => {
    $('uninstall-confirm').disabled = true;
    $('uninstall-confirm').textContent = 'Fermeture…';
    try {
        const { closing } = await getJson('/uninstall', { method: 'POST' });
        if (!closing) {
            closeModal();
            toast('Désinstallation lancée. Arrêtez ce serveur pour qu\'elle puisse se terminer.');
        }
    } catch (err) {
        toast(err.message, true);
        closeModal();
    }
});

document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    closeModal();
    closeHistory();
});

// ---------- Démarrage ----------
getJson('/settings').then(data => { settings = data; renderModels(); }).catch(() => {});
refreshHistory();
