/*!
 * Analytics page JS — draws the click chart using the Canvas API.
 * I didn't want to pull in Chart.js just for one bar chart, so I
 * drew it manually. Took a while to figure out the coordinate math
 * but I'm pretty happy with how it turned out.
 */

(() => {
  'use strict';

  /* copy button on the analytics page (copies the short URL) */
  const copyShortBtn = document.getElementById('copy-short-btn');
  if (copyShortBtn) {
    copyShortBtn.addEventListener('click', async () => {
      const text = copyShortBtn.dataset.copy;
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        const icon = document.getElementById('copy-short-icon');
        if (icon) {
          icon.textContent = 'check';
          setTimeout(() => { icon.textContent = 'content_copy'; }, 1500);
        }
      } catch { /* clipboard access denied, silently ignore */ }
    });
  }

  /* grab the chart data that Flask embedded in the page as JSON */
  const chartDataEl = document.getElementById('chart-data');
  const canvas = document.getElementById('clicks-chart');
  if (!canvas || !chartDataEl) return;

  let chartData;
  try {
    chartData = JSON.parse(chartDataEl.textContent);
  } catch {
    return; // malformed JSON, just don't render the chart
  }

  /**
   * Draws a bar chart on the canvas using the raw click data.
   * Handles high-DPI screens (Retina) by scaling with devicePixelRatio —
   * without this the chart looks blurry on MacBooks. Learned this the hard way.
   *
   * @param {Array<{date: string, clicks: number}>} data - 14 days of click data.
   */
  function drawChart(data) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    // scale up the actual canvas pixels for sharp rendering on high-DPI screens
    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr); // then scale back down in drawing coordinates

    const W = rect.width;
    const H = rect.height;
    const PAD = { top: 20, right: 8, bottom: 36, left: 36 }; // space for labels
    const chartW = W - PAD.left - PAD.right;
    const chartH = H - PAD.top - PAD.bottom;

    // colours that match the CSS theme (--primary is #6366f1)
    const PRIMARY   = '#6366f1';
    const PRIMARY_D = 'rgba(99,102,241,0.12)';
    const GRID_COL  = 'rgba(255,255,255,0.06)';
    const AXIS_COL  = 'rgba(255,255,255,0.25)';
    const LABEL_COL = '#475569';
    const FONT      = "10px 'Ubuntu', system-ui, sans-serif";

    const maxVal = Math.max(...data.map(d => d.clicks), 1); // at least 1 to avoid division by 0
    const n = data.length;
    const barGap = 4;
    const barW = Math.max((chartW - barGap * (n - 1)) / n, 4);

    ctx.clearRect(0, 0, W, H);

    // draw horizontal grid lines with y-axis labels
    const gridLines = 4;
    ctx.font = FONT;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= gridLines; i++) {
      const y = PAD.top + chartH - (i / gridLines) * chartH;
      const val = Math.round((i / gridLines) * maxVal);
      ctx.strokeStyle = GRID_COL;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(PAD.left, y);
      ctx.lineTo(PAD.left + chartW, y);
      ctx.stroke();
      ctx.fillStyle = LABEL_COL;
      ctx.fillText(val, PAD.left - 6, y);
    }

    // draw the bars with a gradient fill (looks nicer than a flat colour)
    data.forEach((d, i) => {
      const x   = PAD.left + i * (barW + barGap);
      const pct = d.clicks / maxVal;
      const bH  = Math.max(pct * chartH, d.clicks > 0 ? 3 : 0); // min 3px height so it's visible
      const y   = PAD.top + chartH - bH;

      const grad = ctx.createLinearGradient(0, y, 0, y + bH);
      grad.addColorStop(0, PRIMARY);
      grad.addColorStop(1, PRIMARY_D);

      const radius = Math.min(4, barW / 2);
      ctx.beginPath();
      ctx.roundRect(x, y, barW, bH, [radius, radius, 0, 0]); // rounded top corners
      ctx.fillStyle = d.clicks > 0 ? grad : GRID_COL; // grey if no clicks that day
      ctx.fill();
    });

    // x-axis date labels — show every other one if there are too many to fit
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = LABEL_COL;
    const showEvery = n <= 7 ? 1 : 2;
    data.forEach((d, i) => {
      if (i % showEvery !== 0) return;
      const x  = PAD.left + i * (barW + barGap) + barW / 2;
      const y  = PAD.top + chartH + 8;
      // append T00:00:00 to avoid timezone offset shifting the date by a day
      const dd = new Date(d.date + 'T00:00:00');
      const label = dd.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      ctx.fillText(label, x, y);
    });
  }

  drawChart(chartData);

  // redraw when the container is resized so the chart stays responsive
  const ro = new ResizeObserver(() => drawChart(chartData));
  ro.observe(canvas.parentElement);

})();
