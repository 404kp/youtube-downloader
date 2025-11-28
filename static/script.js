let loadedVideos = [];

async function loadVideos() {
    const urlInput = document.getElementById('urlInput');
    const urls = urlInput.value.split('\n').filter(url => url.trim() !== '');
    
    if (urls.length === 0) {
        alert('Bitte gib mindestens eine URL ein.');
        return;
    }

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    
    try {
        const response = await fetch('/get_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: urls })
        });

        const data = await response.json();
        
        if (response.ok) {
            loadedVideos = data.videos;
            renderVideos(loadedVideos);
            document.getElementById('resultsSection').classList.remove('hidden');
        } else {
            alert('Fehler: ' + (data.error || 'Unbekannter Fehler'));
        }
    } catch (error) {
        alert('Netzwerkfehler: ' + error.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

function renderVideos(videos) {
    const list = document.getElementById('videoList');
    list.innerHTML = '';

    videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'video-card';
        
        // Use a placeholder if thumbnail is empty
        const thumbSrc = video.thumbnail || 'https://via.placeholder.com/120x68?text=No+Thumb';

        card.innerHTML = `
            <img src="${thumbSrc}" alt="Thumbnail" class="video-thumb">
            <div class="video-info">
                <div class="video-title" title="${video.title}">${video.title}</div>
                <div class="video-meta">${video.uploader} • ${video.duration}</div>
            </div>
            <div class="video-actions">
                <button onclick="downloadSingle('${video.url}', 'mp3')" class="mini-btn action-btn mp3" title="MP3 herunterladen"><i class="fas fa-music"></i></button>
                <button onclick="downloadSingle('${video.url}', 'mp4')" class="mini-btn action-btn mp4" title="MP4 herunterladen"><i class="fas fa-video"></i></button>
            </div>
        `;
        list.appendChild(card);
    });
}

async function downloadSingle(url, format) {
    // Trigger download
    // We can't easily use fetch for file download if we want the browser to handle the save dialog nicely without blobs for large files.
    // But for single files, creating a form and submitting it is a classic way, or using fetch and blob.
    // Let's use fetch + blob to handle errors better, or just window.location if it was a GET.
    // Since it's POST, let's use a temporary form submission or fetch-blob.
    
    // Using fetch to catch errors first
    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
        const response = await fetch('/download_single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, format: format })
        });

        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            // Try to get filename from header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'download.' + format;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch.length === 2)
                    filename = filenameMatch[1];
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } else {
            const err = await response.json();
            alert('Fehler beim Download: ' + (err.error || 'Unbekannt'));
        }
    } catch (e) {
        alert('Fehler: ' + e.message);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

async function downloadAll(format) {
    if (loadedVideos.length === 0) return;

    const urls = loadedVideos.map(v => v.url);
    
    // Show global loading state if desired, or just alert
    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verarbeite...';
    btn.disabled = true;

    try {
        const response = await fetch('/download_all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls: urls, format: format })
        });

        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `downloads_${format}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } else {
            const err = await response.json();
            alert('Fehler beim Download: ' + (err.error || 'Unbekannt'));
        }
    } catch (e) {
        alert('Fehler: ' + e.message);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}
