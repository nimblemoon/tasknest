/* TaskNest — small, framework-free interactions. */
(function () {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  /* ------------------------------------------------------------------ */
  /* Sidebar drawer (mobile)                                             */
  /* ------------------------------------------------------------------ */
  const sidebar = document.querySelector('[data-sidebar]');
  const scrim = document.querySelector('[data-sidebar-close]');

  const openSidebar = () => {
    if (!sidebar) return;
    sidebar.classList.add('is-open');
    if (scrim) {
      scrim.classList.add('is-open');
      scrim.removeAttribute('hidden');
    }
    document.body.style.overflow = 'hidden';
  };

  const closeSidebar = () => {
    if (!sidebar) return;
    sidebar.classList.remove('is-open');
    if (scrim) {
      scrim.classList.remove('is-open');
      scrim.setAttribute('hidden', '');
    }
    document.body.style.overflow = '';
  };

  document.addEventListener('click', (event) => {
    const opener = event.target.closest('[data-sidebar-open]');
    if (opener) {
      event.preventDefault();
      openSidebar();
      return;
    }
    const closer = event.target.closest('[data-sidebar-close]');
    if (closer && closer !== scrim) {
      // allow scrim click
    }
    if (event.target === scrim) {
      closeSidebar();
    }
  });

  // Close sidebar on Escape and on navigation.
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeSidebar();
  });

  /* ------------------------------------------------------------------ */
  /* Modal dialogs                                                       */
  /* ------------------------------------------------------------------ */
  const openDialog = (name) => {
    const dialog = document.getElementById(name);
    if (dialog && typeof dialog.showModal === 'function') {
      try { dialog.showModal(); } catch (e) { dialog.setAttribute('open', ''); }
    } else if (dialog) {
      dialog.setAttribute('open', '');
    }
  };

  const closeDialog = (dialog) => {
    if (!dialog) return;
    if (typeof dialog.close === 'function') {
      try { dialog.close(); return; } catch (e) { /* fall through */ }
    }
    dialog.removeAttribute('open');
  };

  document.addEventListener('click', (event) => {
    const opener = event.target.closest('[data-open-dialog]');
    if (opener) {
      event.preventDefault();
      openDialog(opener.getAttribute('data-open-dialog'));
      return;
    }
    const closer = event.target.closest('[data-close-dialog]');
    if (closer) {
      event.preventDefault();
      closeDialog(closer.closest('dialog'));
      return;
    }
  });

  // Close <dialog> on backdrop click.
  document.addEventListener('click', (event) => {
    const dialog = event.target.closest('dialog');
    if (dialog && event.target === dialog) closeDialog(dialog);
  });

  /* ------------------------------------------------------------------ */
  /* Flash messages                                                      */
  /* ------------------------------------------------------------------ */
  const dismissFlash = (flash) => {
    if (!flash) return;
    flash.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
    flash.style.opacity = '0';
    flash.style.transform = 'translateY(-6px)';
    setTimeout(() => flash.remove(), 220);
  };

  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-dismiss-flash]');
    if (button) {
      event.preventDefault();
      dismissFlash(button.closest('.flash'));
    }
  });

  // Auto-dismiss after a few seconds.
  $$('.flash').forEach((flash) => {
    setTimeout(() => dismissFlash(flash), 5200);
  });

  /* ------------------------------------------------------------------ */
  /* Focus timer                                                         */
  /* ------------------------------------------------------------------ */
  const timerRoot = document.querySelector('[data-focus-timer]');
  if (timerRoot) {
    const timeEl = timerRoot.querySelector('[data-focus-time]');
    const barEl = timerRoot.querySelector('[data-focus-bar]');
    const startBtn = timerRoot.querySelector('[data-focus-start]');
    const startLabel = timerRoot.querySelector('[data-focus-start-label]');
    const resetBtn = timerRoot.querySelector('[data-focus-reset]');
    const switchBtn = timerRoot.querySelector('[data-focus-switch]');
    const modeBadge = timerRoot.querySelector('[data-focus-mode]');

    let duration = parseInt(timerRoot.getAttribute('data-duration') || '25', 10) * 60;
    let remaining = duration;
    let running = false;
    let interval = null;
    let isBreak = false;

    const format = (seconds) => {
      const m = Math.floor(seconds / 60);
      const s = seconds % 60;
      return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    };

    const render = () => {
      if (timeEl) timeEl.textContent = format(remaining);
      if (barEl) {
        const pct = ((duration - remaining) / duration) * 100;
        barEl.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
      if (startLabel) startLabel.textContent = running ? 'Pause' : 'Start';
      if (startBtn) {
        startBtn.classList.toggle('is-running', running);
      }
      document.title = (running ? format(remaining) + ' · ' : '') + 'TaskNest';
    };

    const tick = () => {
      if (remaining <= 0) {
        running = false;
        clearInterval(interval);
        interval = null;
        if (!isBreak) {
          const minutes = Math.round(duration / 60);
          const csrfToken = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1];
          fetch('/tasks/focus-sessions/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken || '',
            },
            body: JSON.stringify({ duration_minutes: minutes }),
            credentials: 'same-origin',
          }).catch(() => {});
        }
        // Gentle chime via Web Audio (best effort).
        try {
          const ctx = new (window.AudioContext || window.webkitAudioContext)();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain); gain.connect(ctx.destination);
          osc.frequency.value = 660;
          gain.gain.setValueAtTime(0.12, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
          osc.start(); osc.stop(ctx.currentTime + 0.6);
        } catch (e) { /* no audio */ }
        return;
      }
      remaining -= 1;
      render();
    };

    const start = () => {
      if (running) {
        running = false;
        clearInterval(interval);
        interval = null;
      } else {
        running = true;
        interval = setInterval(tick, 1000);
      }
      render();
    };

    const reset = () => {
      running = false;
      clearInterval(interval);
      interval = null;
      remaining = duration;
      render();
    };

    const switchMode = () => {
      isBreak = !isBreak;
      duration = (isBreak ? 5 : 25) * 60;
      remaining = duration;
      running = false;
      clearInterval(interval);
      interval = null;
      if (modeBadge) modeBadge.textContent = isBreak ? 'Break' : 'Deep work';
      if (switchBtn) switchBtn.textContent = isBreak ? 'Back to work' : 'Take a break';
      render();
    };

    if (startBtn) startBtn.addEventListener('click', start);
    if (resetBtn) resetBtn.addEventListener('click', reset);
    if (switchBtn) switchBtn.addEventListener('click', switchMode);

    render();
  }

  /* ------------------------------------------------------------------ */
  /* Keyboard shortcuts                                                  */
  /* ------------------------------------------------------------------ */
  const isTyping = (target) => {
    if (!target) return false;
    const tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable;
  };

  document.addEventListener('keydown', (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (isTyping(event.target)) return;

    if (event.key === 'n' || event.key === 'N') {
      event.preventDefault();
      const dialog = document.getElementById('quick-add');
      if (dialog) openDialog('quick-add');
      else window.location.href = '/tasks/add/';
      return;
    }

    if (event.key === '/') {
      event.preventDefault();
      const search = document.querySelector('.global-search input');
      if (search) search.focus();
      return;
    }

    if (event.key === 'g') {
      // two-key combos: wait for next key
      const handler = (e2) => {
        document.removeEventListener('keydown', handler);
        if (e2.key === 'd') window.location.href = '/tasks/';
        else if (e2.key === 'b') window.location.href = '/tasks/board/';
        else if (e2.key === 'c') window.location.href = '/tasks/calendar/';
        else if (e2.key === 'i') window.location.href = '/tasks/insights/';
      };
      document.addEventListener('keydown', handler, { once: true });
      setTimeout(() => document.removeEventListener('keydown', handler), 1200);
    }
  });

  /* ------------------------------------------------------------------ */
  /* Auto-focus quick add title when opened                               */
  /* ------------------------------------------------------------------ */
  document.addEventListener('shown', (e) => {}, true);
  const quickDialog = document.getElementById('quick-add');
  if (quickDialog) {
    quickDialog.addEventListener('close', () => {});
    const observer = new MutationObserver(() => {
      if (quickDialog.hasAttribute('open') || quickDialog.open) {
        const input = quickDialog.querySelector('input[name="title"]');
        if (input) setTimeout(() => input.focus(), 50);
      }
    });
    observer.observe(quickDialog, { attributes: true });
  }

  /* ------------------------------------------------------------------ */
  /* Smooth in-page anchor for project dialog on projects page            */
  /* ------------------------------------------------------------------ */
  if (window.location.hash === '#new-project') {
    openDialog('project-dialog');
  }
})();
