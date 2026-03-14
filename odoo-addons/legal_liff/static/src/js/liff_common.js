/**
 * LIFF Common Utilities
 * Shared across all LIFF pages
 */
var LiffApp = (function() {
    var _profile = null;
    var _initialized = false;

    function getLiffId() {
        var meta = document.querySelector('meta[name="liff-id"]');
        return meta ? meta.getAttribute('content') : '0000000000-xxxxxxxx';
    }

    async function init() {
        if (_initialized) return _profile;
        try {
            // Timeout LIFF init after 3 seconds to prevent hanging
            await Promise.race([
                liff.init({ liffId: getLiffId() }),
                new Promise(function(_, reject) {
                    setTimeout(function() { reject(new Error('LIFF init timeout')); }, 3000);
                })
            ]);
            _initialized = true;
            if (liff.isLoggedIn()) {
                _profile = await liff.getProfile();
            }
        } catch(e) {
            console.log('LIFF init error:', e);
        }
        return _profile;
    }

    function getProfile() {
        return _profile;
    }

    function getUserId() {
        return _profile ? _profile.userId : '';
    }

    function closeWindow() {
        try {
            if (typeof liff !== 'undefined' && liff.isInClient()) {
                liff.closeWindow();
            } else {
                window.close();
            }
        } catch(e) {
            window.close();
        }
    }

    async function fetchJson(url, data) {
        var resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: data }),
        });
        var json = await resp.json();
        if (json.error) {
            throw new Error(json.error.message || 'Server error');
        }
        return json.result;
    }

    function showLoading(el) {
        if (el) el.innerHTML = '<div class="liff-spinner"></div>';
    }

    function formatDate(dtStr) {
        if (!dtStr) return '-';
        var d = new Date(dtStr);
        return d.toLocaleDateString('th-TH', {
            year: 'numeric', month: 'short', day: 'numeric',
        });
    }

    function formatDateTime(dtStr) {
        if (!dtStr) return '-';
        var d = new Date(dtStr);
        return d.toLocaleDateString('th-TH', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    }

    return {
        init: init,
        getProfile: getProfile,
        getUserId: getUserId,
        closeWindow: closeWindow,
        fetchJson: fetchJson,
        showLoading: showLoading,
        formatDate: formatDate,
        formatDateTime: formatDateTime,
    };
})();
