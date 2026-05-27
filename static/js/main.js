(() => {
  'use strict';

  /* ── Element references ──────────────────────────────── */
  const form        = document.getElementById('shorten-form');
  const urlInput    = document.getElementById('long-url-input');
  const pasteBtn    = document.getElementById('paste-btn');
  const pasteIcon   = document.getElementById('paste-icon');
  const aliasToggle = document.getElementById('alias-toggle');
  const switchEl    = document.getElementById('switch');
  const aliasGroup  = document.getElementById('alias-group');
  const aliasInput  = document.getElementById('custom-alias-input');
  const submitBtn   = document.getElementById('submit-btn');
  const resultBox   = document.getElementById('result');

  /* ── State ───────────────────────────────────────────── */
  let aliasEnabled = false;
  let isSubmitting = false;

  /* ── Custom alias toggle ─────────────────────────────── */
  function toggleAlias() {
    aliasEnabled = !aliasEnabled;
    switchEl.classList.toggle('active', aliasEnabled);
    aliasGroup.classList.toggle('visible', aliasEnabled);
    aliasToggle.setAttribute('aria-checked', String(aliasEnabled));
    aliasGroup.setAttribute('aria-hidden', String(!aliasEnabled));

    if (!aliasEnabled) {
      aliasInput.value = '';
      aliasInput.classList.remove('invalid');
    } else {
      setTimeout(() => aliasInput.focus(), 320);
    }
  }

  aliasToggle.addEventListener('click', toggleAlias);

  aliasToggle.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      toggleAlias();
    }
  });

  /* ── Paste button ────────────────────────────────────── */
  pasteBtn.addEventListener('click', async () => {
    if (!navigator.clipboard?.readText) { urlInput.focus(); return; }
    try {
      const text = (await navigator.clipboard.readText()).trim();
      if (text) {
        urlInput.value = text;
        urlInput.classList.remove('invalid');
        pasteIcon.textContent = 'check';
        setTimeout(() => { pasteIcon.textContent = 'content_paste'; }, 1200);
      }
    } catch {
      urlInput.focus();
    }
  });

  /* ── Validation helpers ──────────────────────────────── */
  const ALIAS_REGEX = /^[a-zA-Z0-9]+$/;

  function validateUrl(value) {
    if (!value) return 'Please enter a URL.';
    const withScheme = /^https?:\/\//i.test(value) ? value : `https://${value}`;
    try {
      const parsed = new URL(withScheme);
      if (!parsed.hostname.includes('.')) {
        return 'Please enter a valid URL (e.g., https://example.com).';
      }
    } catch {
      return 'Please enter a valid URL.';
    }
    return null;
  }

  function validateAlias(value) {
    if (!value) return 'Custom alias cannot be empty.';
    if (!ALIAS_REGEX.test(value)) return 'Alias must contain only letters and numbers.';
    if (value.length < 4 || value.length > 30) return 'Alias must be between 4 and 30 characters.';
    return null;
  }

  /* ── Result rendering ────────────────────────────────── */
  function showResult(type, html) {
    resultBox.innerHTML = `
      <div class="result-inner ${type}">
        <p class="result-label">${type === 'success' ? 'Your short URL' : 'Error'}</p>
        ${html}
      </div>`;
    resultBox.classList.add('visible');
  }

  function showSuccess(shortUrl) {
    const shortCode    = shortUrl.split('/').filter(Boolean).pop();
    const analyticsHref = `/analytics/${shortCode}`;

    showResult('success', `
      <div class="short-url-row">
        <a class="short-url-link" href="${escapeHtml(shortUrl)}" target="_blank" rel="noopener noreferrer">
          ${escapeHtml(shortUrl)}
        </a>
        <button type="button" class="icon-btn" id="copy-btn" title="Copy to clipboard" aria-label="Copy short URL">
          <span class="material-symbols-outlined" id="copy-icon">content_copy</span>
        </button>
        <a class="analytics-link" href="${escapeHtml(analyticsHref)}" target="_blank" rel="noopener noreferrer" title="View analytics">
          <span class="material-symbols-outlined" style="font-size:14px">bar_chart</span>
          Analytics
        </a>
      </div>`);

    document.getElementById('copy-btn').addEventListener('click', () => copyToClipboard(shortUrl));
  }

  function showError(message) {
    showResult('error', `<p class="error-message">${escapeHtml(message)}</p>`);
  }

  function hideResult() {
    resultBox.classList.remove('visible');
  }

  /* ── Copy to clipboard ───────────────────────────────── */
  async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      const icon = document.getElementById('copy-icon');
      if (icon) {
        icon.textContent = 'check';
        setTimeout(() => { if (icon) icon.textContent = 'content_copy'; }, 1200);
      }
    } catch { /* silently ignore */ }
  }

  /* ── Loading state ───────────────────────────────────── */
  function setLoading(loading) {
    isSubmitting = loading;
    submitBtn.disabled = loading;
    submitBtn.classList.toggle('loading', loading);
  }

  /* ── Form submission ─────────────────────────────────── */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const rawUrl   = urlInput.value.trim();
    const rawAlias = aliasEnabled ? aliasInput.value.trim() : '';

    const urlError = validateUrl(rawUrl);
    if (urlError) {
      urlInput.classList.add('invalid');
      showError(urlError);
      urlInput.focus();
      return;
    }
    urlInput.classList.remove('invalid');

    if (aliasEnabled) {
      const aliasError = validateAlias(rawAlias);
      if (aliasError) {
        aliasInput.classList.add('invalid');
        showError(aliasError);
        aliasInput.focus();
        return;
      }
      aliasInput.classList.remove('invalid');
    }

    const payload = { long_url: rawUrl };
    if (aliasEnabled && rawAlias) payload.custom_alias = rawAlias;

    setLoading(true);
    hideResult();

    try {
      const response = await fetch('/api/shorten', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok && data.short_url) {
        showSuccess(data.short_url);
      } else {
        const message = data?.error || `Unexpected error (HTTP ${response.status}).`;
        showError(message);
        if (response.status === 409 || message.toLowerCase().includes('alias')) {
          aliasInput.classList.add('invalid');
          aliasInput.focus();
        }
      }
    } catch {
      showError('Network error — please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  });

  /* ── Clear invalid state on input ───────────────────── */
  urlInput.addEventListener('input',   () => urlInput.classList.remove('invalid'));
  aliasInput.addEventListener('input', () => aliasInput.classList.remove('invalid'));

  /* ── XSS guard ───────────────────────────────────────── */
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
      .replace(/'/g,  '&#39;');
  }

})();
