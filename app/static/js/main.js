/*!
 * Shortly — main page JavaScript
 * Handles: form submit, URL/alias validation, toggle animations, clipboard, result display.
 * Zero dependencies — vanilla JS only. I tried to keep this readable.
 */

(() => {
  'use strict';

  /* grab all the DOM elements I'll need */
  const form        = document.getElementById('shorten-form');
  const urlInput    = document.getElementById('long-url-input');
  const pasteBtn    = document.getElementById('paste-btn');
  const pasteIcon   = document.getElementById('paste-icon');
  const aliasToggle = document.getElementById('alias-toggle');
  const aliasGroup  = document.getElementById('alias-group');
  const aliasInput  = document.getElementById('custom-alias-input');
  const expiryToggle = document.getElementById('expiry-toggle');
  const expiryGroup = document.getElementById('expiry-group');
  const ttlSelect   = document.getElementById('ttl-select');
  const submitBtn   = document.getElementById('submit-btn');
  const resultArea  = document.getElementById('result-area');

  /* track state */
  let isSubmitting  = false;
  let aliasEnabled  = false;
  let expiryEnabled = false;

  /* ── Helpers ─────────────────────────────────────────────────────────── */

  /**
   * Escapes HTML characters before inserting user-provided strings into the DOM.
   * Without this, someone could submit a URL like <script>alert('xss')</script>
   * and it would actually execute. Learned about XSS the fun way 😬
   *
   * @param {string} str - raw string from user or API
   * @returns {string} safe string for innerHTML
   */
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /**
   * Shows or clears a validation error on a form field.
   * Adds/removes the 'invalid' CSS class and updates the error message element.
   *
   * @param {HTMLElement} inputEl - the input to mark as invalid
   * @param {HTMLElement} errorEl - where to put the error text
   * @param {string|null} message - error message, or falsy to clear
   */
  function setFieldError(inputEl, errorEl, message) {
    if (message) {
      inputEl?.classList.add('invalid');
      if (errorEl) errorEl.textContent = message;
    } else {
      inputEl?.classList.remove('invalid');
      if (errorEl) errorEl.textContent = '';
    }
  }

  /** Clears all validation errors on the form. */
  function clearAllErrors() {
    setFieldError(urlInput, document.getElementById('url-error'), '');
    setFieldError(aliasInput, document.getElementById('alias-error'), '');
  }

  /* ── Toggle switch logic ─────────────────────────────────────────────── */
  function setToggle(btn, group, enabled) {
    btn.setAttribute('aria-checked', String(enabled));
    group.classList.toggle('open', enabled);
    group.setAttribute('aria-hidden', String(!enabled));
  }

  function handleToggle(btn, group, current) {
    const next = !current;
    setToggle(btn, group, next);
    return next;
  }

  aliasToggle.addEventListener('click', () => {
    aliasEnabled = handleToggle(aliasToggle, aliasGroup, aliasEnabled);
    if (!aliasEnabled) {
      aliasInput.value = '';
      setFieldError(aliasInput, document.getElementById('alias-error'), '');
    } else {
      setTimeout(() => aliasInput.focus(), 320); // wait for CSS transition to finish
    }
  });

  aliasToggle.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); aliasToggle.click(); }
  });

  expiryToggle.addEventListener('click', () => {
    expiryEnabled = handleToggle(expiryToggle, expiryGroup, expiryEnabled);
  });

  expiryToggle.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); expiryToggle.click(); }
  });

  /* ── Paste button ────────────────────────────────────────────────────── */
  pasteBtn.addEventListener('click', async () => {
    if (!navigator.clipboard?.readText) { urlInput.focus(); return; }
    try {
      const text = (await navigator.clipboard.readText()).trim();
      if (text) {
        urlInput.value = text;
        urlInput.classList.remove('invalid');
        pasteIcon.textContent = 'check';
        setTimeout(() => { pasteIcon.textContent = 'content_paste'; }, 1500);
      }
    } catch {
      urlInput.focus(); // clipboard permission denied, just focus the input
    }
  });

  /* ── Client-side validation ──────────────────────────────────────────── */

  // quick regex for basic URL shape — the backend does a more thorough check
  const URL_REGEX = /^(https?:\/\/)?([\w-]+\.)+[\w-]+(\/[^\s]*)?$/i;
  const ALIAS_REGEX = /^[a-zA-Z0-9_-]+$/;

  /**
   * Quick URL check on the client side before hitting the API.
   * Mirrors the logic in validators.py — if it passes here it should
   * pass on the server too (but server always validates anyway).
   *
   * @param {string} value - URL input from user
   * @returns {string|null} error message, or null if valid
   */
  function validateUrl(value) {
    if (!value) return 'Please enter a URL.';
    const withScheme = /^https?:\/\//i.test(value) ? value : `https://${value}`;
    try {
      const u = new URL(withScheme);
      if (!u.hostname.includes('.') && u.hostname !== 'localhost') {
        return 'Please enter a valid URL (e.g., https://example.com).';
      }
    } catch {
      return 'Please enter a valid URL.';
    }
    return null;
  }

  /**
   * Quick alias validation. Same rules as the backend — letters, numbers,
   * hyphens, underscores, 4–30 chars.
   *
   * @param {string} value - alias input from user
   * @returns {string|null} error message, or null if valid
   */
  function validateAlias(value) {
    if (!value) return 'Custom alias cannot be empty.';
    if (!ALIAS_REGEX.test(value)) return 'Alias may only contain letters, numbers, hyphens, and underscores.';
    if (value.length < 4 || value.length > 30) return 'Alias must be between 4 and 30 characters.';
    return null;
  }

  /* ── Result rendering ────────────────────────────────────────────────── */

  /**
   * Renders the success state after a URL is shortened.
   * Builds the HTML with the short URL, copy button, QR code, and expiry info.
   * Everything goes through escapeHtml() before hitting innerHTML.
   *
   * @param {Object} data - response from /api/shorten
   */
  function showSuccess(data) {
    const { short_url, analytics_url, qr_code, expires_at } = data;
    const shortCode = short_url.split('/').filter(Boolean).pop();

    let expiryHtml = '';
    if (expires_at) {
      const d = new Date(expires_at).toLocaleDateString(undefined, { dateStyle: 'medium' });
      expiryHtml = `
        <p class="result-expiry">
          <span class="material-symbols-outlined">timer</span>
          Expires ${escapeHtml(d)}
        </p>`;
    }

    let qrHtml = '';
    if (qr_code) {
      qrHtml = `
        <div class="result-qr-row">
          <img class="result-qr-img" src="${escapeHtml(qr_code)}" alt="QR code" width="64" height="64" />
          <span class="result-qr-label">Scan to visit · <a href="${escapeHtml(analytics_url)}" target="_blank" rel="noopener noreferrer" style="color:var(--primary)">View analytics</a></span>
        </div>`;
    }

    resultArea.innerHTML = `
      <div class="result-success">
        <p class="result-label">
          <span class="material-symbols-outlined" style="font-size:13px;font-variation-settings:'FILL' 1,'wght' 500,'GRAD' 0,'opsz' 20">check_circle</span>
          Your short URL
        </p>
        <div class="result-url-row">
          <a class="result-short-url" href="${escapeHtml(short_url)}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(short_url)}
          </a>
          <div class="result-actions">
            <button type="button" class="icon-btn" id="copy-result-btn" aria-label="Copy short URL" style="width:34px;height:34px;border-radius:8px">
              <span class="material-symbols-outlined" id="copy-result-icon" style="font-size:16px">content_copy</span>
            </button>
            <a class="analytics-pill" href="${escapeHtml(analytics_url)}" target="_blank" rel="noopener noreferrer">
              <span class="material-symbols-outlined">bar_chart</span>
              Stats
            </a>
          </div>
        </div>
        ${expiryHtml}
        ${qrHtml}
      </div>`;

    resultArea.classList.add('visible');

    // attach copy handler to the freshly created button
    document.getElementById('copy-result-btn')?.addEventListener('click', () => {
      copyText(short_url, 'copy-result-icon');
    });
  }

  /**
   * Shows an error message in the result area.
   * Usually from the API when validation fails server-side.
   *
   * @param {string} message - error to display
   */
  function showError(message) {
    resultArea.innerHTML = `
      <div class="result-error">
        <p class="result-error-label">Error</p>
        <p class="result-error-msg">${escapeHtml(message)}</p>
      </div>`;
    resultArea.classList.add('visible');
  }

  function hideResult() {
    resultArea.classList.remove('visible');
    // clear innerHTML after transition so it doesn't flash old content
    setTimeout(() => { if (!resultArea.classList.contains('visible')) resultArea.innerHTML = ''; }, 400);
  }

  /* ── Clipboard copy ──────────────────────────────────────────────────── */
  async function copyText(text, iconId) {
    try {
      await navigator.clipboard.writeText(text);
      const icon = document.getElementById(iconId);
      if (icon) {
        icon.textContent = 'check';
        setTimeout(() => { if (icon) icon.textContent = 'content_copy'; }, 1500);
      }
    } catch { /* clipboard write failed, silently ignore */ }
  }

  /* ── Submit button loading state ─────────────────────────────────────── */

  /**
   * Disables the submit button while a request is in flight.
   * Prevents double-submitting if the user rage-clicks the button.
   *
   * @param {boolean} loading - true while waiting for API response
   */
  function setLoading(loading) {
    isSubmitting = loading;
    submitBtn.disabled = loading;
    submitBtn.setAttribute('aria-busy', String(loading));
    submitBtn.classList.toggle('loading', loading);
  }

  /* ── Form submission ─────────────────────────────────────────────────── */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isSubmitting) return; // ignore if already submitting

    clearAllErrors();
    hideResult();

    const rawUrl   = urlInput.value.trim();
    const rawAlias = aliasEnabled ? aliasInput.value.trim() : '';

    // validate on client first — faster feedback than waiting for API round-trip
    const urlErr = validateUrl(rawUrl);
    if (urlErr) {
      setFieldError(urlInput, document.getElementById('url-error'), urlErr);
      urlInput.focus();
      return;
    }

    if (aliasEnabled) {
      const aliasErr = validateAlias(rawAlias);
      if (aliasErr) {
        setFieldError(aliasInput, document.getElementById('alias-error'), aliasErr);
        aliasInput.focus();
        return;
      }
    }

    const payload = { long_url: rawUrl };
    if (aliasEnabled && rawAlias) payload.custom_alias = rawAlias;
    if (expiryEnabled && ttlSelect) payload.ttl_days = parseInt(ttlSelect.value, 10);

    setLoading(true);

    try {
      const response = await fetch('/api/shorten', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const json = await response.json();

      if (response.ok && json.data?.short_url) {
        showSuccess(json.data);
      } else {
        const msg = json.error || `Unexpected error (HTTP ${response.status}).`;
        showError(msg);

        // highlight the alias field if that's what caused the conflict
        if (response.status === 409 || msg.toLowerCase().includes('alias')) {
          setFieldError(aliasInput, document.getElementById('alias-error'), msg);
          aliasInput.focus();
        }
      }
    } catch {
      showError('Network error — please check your connection and try again.');
    } finally {
      setLoading(false); // always re-enable the button
    }
  });

  /* clear field errors as soon as the user starts typing again */
  urlInput.addEventListener('input', () => {
    setFieldError(urlInput, document.getElementById('url-error'), '');
  });
  aliasInput?.addEventListener('input', () => {
    setFieldError(aliasInput, document.getElementById('alias-error'), '');
  });

})();
