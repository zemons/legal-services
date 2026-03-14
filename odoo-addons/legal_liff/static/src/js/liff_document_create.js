/**
 * LIFF Document Create Page
 * No LIFF SDK dependency — works in any browser including LINE in-app browser
 */

var allTemplates = [];
var allCases = [];
var currentTemplate = null;

function onCategoryChange() {
    var cat = document.getElementById('sel-category').value;
    var tmplField = document.getElementById('tmpl-field');
    var sel = document.getElementById('sel-template');

    if (!cat) {
        tmplField.style.display = 'none';
        document.getElementById('dynamic-fields').innerHTML = '';
        document.getElementById('submit-area').style.display = 'none';
        document.getElementById('case-field').style.display = 'none';
        return;
    }

    var filtered = allTemplates.filter(function(t) { return t.category === cat; });
    sel.innerHTML = '<option value="">-- เลือกรูปแบบ --</option>';
    filtered.forEach(function(t) {
        sel.innerHTML += '<option value="' + t.id + '">' + escHtml(t.name) + '</option>';
    });
    tmplField.style.display = 'block';
    document.getElementById('tmpl-desc').textContent = '';
    document.getElementById('dynamic-fields').innerHTML = '';
    document.getElementById('submit-area').style.display = 'none';
    document.getElementById('case-field').style.display = 'none';
    currentTemplate = null;
}

function onTemplateChange() {
    var tmplId = parseInt(document.getElementById('sel-template').value);
    var container = document.getElementById('dynamic-fields');
    container.innerHTML = '';
    currentTemplate = null;

    if (!tmplId) {
        document.getElementById('tmpl-desc').textContent = '';
        document.getElementById('submit-area').style.display = 'none';
        document.getElementById('case-field').style.display = 'none';
        return;
    }

    var tmpl = allTemplates.find(function(t) { return t.id === tmplId; });
    if (!tmpl) return;
    currentTemplate = tmpl;

    document.getElementById('tmpl-desc').textContent = tmpl.description || '';

    if (allCases.length > 0) {
        document.getElementById('case-field').style.display = 'block';
    }

    // Render dynamic form fields
    var fields = tmpl.required_fields || [];
    var html = '';
    fields.forEach(function(f) {
        var showWhenAttr = '';
        if (f.show_when) {
            showWhenAttr = ' data-show-when="' + escAttr(JSON.stringify(f.show_when)) + '" style="display:none"';
        }
        html += '<div class="liff-field"' + showWhenAttr + '>';
        html += '<label>' + escHtml(f.label);
        if (f.required) html += ' <span class="text-danger">*</span>';
        html += '</label>';

        var req = f.required ? ' required' : '';
        var nm = escAttr(f.name);

        if (f.type === 'textarea') {
            html += '<textarea name="' + nm + '" rows="4"' + req + '></textarea>';
        } else if (f.type === 'date') {
            html += '<input type="date" name="' + nm + '"' + req + '/>';
        } else if (f.type === 'number') {
            html += '<input type="number" name="' + nm + '"' + req + '/>';
        } else if (f.type === 'select' && f.options) {
            html += '<select name="' + nm + '"' + req + '>';
            html += '<option value="">-- เลือก --</option>';
            f.options.forEach(function(opt) {
                html += '<option value="' + escAttr(opt) + '">' + escHtml(opt) + '</option>';
            });
            html += '</select>';
        } else if (f.type === 'address') {
            html += '<div class="addr-group" data-field="' + nm + '">';
            html += '<input type="text" class="addr-house" placeholder="เลขที่ หมู่ ซอย ถนน"' + req + '/>';
            html += '<input type="text" class="addr-search" placeholder="พิมพ์ชื่อตำบล/อำเภอ เพื่อค้นหา..." autocomplete="off"/>';
            html += '<div class="addr-results" style="display:none;max-height:200px;overflow-y:auto;border:1px solid #dfe6e9;border-radius:6px;background:#fff;"></div>';
            html += '<div class="addr-selected" style="display:none;padding:8px;background:#f0f9f0;border-radius:6px;margin-top:4px;font-size:14px;"></div>';
            html += '<input type="hidden" name="' + nm + '"/>';
            html += '</div>';
        } else {
            html += '<input type="text" name="' + nm + '"' + req + '/>';
        }

        html += '</div>';
    });
    container.innerHTML = html;
    document.getElementById('submit-area').style.display = 'block';

    // Initialize address autocomplete fields
    container.querySelectorAll('.addr-group').forEach(initAddressField);

    // Initialize conditional field visibility
    initConditionalFields(container);
}

// ── Conditional Fields (show_when) ────────────────────────

function initConditionalFields(container) {
    var conditionalDivs = container.querySelectorAll('[data-show-when]');
    if (conditionalDivs.length === 0) return;

    // Find all controlling field names referenced in show_when
    var controllingNames = {};
    conditionalDivs.forEach(function(div) {
        try {
            var cond = JSON.parse(div.getAttribute('data-show-when'));
            Object.keys(cond).forEach(function(k) { controllingNames[k] = true; });
        } catch(e) {}
    });

    // Attach change listeners to controlling fields
    Object.keys(controllingNames).forEach(function(fieldName) {
        var el = container.querySelector('[name="' + fieldName + '"]');
        if (el) {
            el.addEventListener('change', function() {
                applyConditionalVisibility(container);
            });
        }
    });

    // Apply initial state
    applyConditionalVisibility(container);
}

function applyConditionalVisibility(container) {
    container.querySelectorAll('[data-show-when]').forEach(function(div) {
        try {
            var cond = JSON.parse(div.getAttribute('data-show-when'));
            var visible = true;
            Object.keys(cond).forEach(function(fieldName) {
                var el = container.querySelector('[name="' + fieldName + '"]');
                if (!el || el.value !== cond[fieldName]) {
                    visible = false;
                }
            });
            div.style.display = visible ? '' : 'none';
            // Clear values of hidden fields to avoid stale data
            if (!visible) {
                div.querySelectorAll('input, textarea, select').forEach(function(inp) {
                    if (inp.type !== 'hidden') inp.value = '';
                });
            }
        } catch(e) {
            div.style.display = '';
        }
    });
}

// ── Address Autocomplete ──────────────────────────────────

function initAddressField(group) {
    var searchInput = group.querySelector('.addr-search');
    var resultsDiv = group.querySelector('.addr-results');
    var selectedDiv = group.querySelector('.addr-selected');
    var hiddenInput = group.querySelector('input[type="hidden"]');
    var houseInput = group.querySelector('.addr-house');
    var debounceTimer = null;

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        var q = searchInput.value.trim();
        if (q.length < 2) { resultsDiv.style.display = 'none'; return; }
        debounceTimer = setTimeout(function() { searchAddress(q); }, 300);
    });

    searchInput.addEventListener('focus', function() {
        if (resultsDiv.children.length > 0) resultsDiv.style.display = 'block';
    });

    document.addEventListener('click', function(e) {
        if (!group.contains(e.target)) resultsDiv.style.display = 'none';
    });

    function searchAddress(q) {
        callApi('/liff/address/search', { q: q, limit: 15 }).then(function(res) {
            var items = res.results || [];
            resultsDiv.innerHTML = '';
            if (items.length === 0) {
                resultsDiv.innerHTML = '<div style="padding:8px;color:#999;">ไม่พบผลลัพธ์</div>';
                resultsDiv.style.display = 'block';
                return;
            }
            items.forEach(function(addr) {
                var item = document.createElement('div');
                item.style.cssText = 'padding:8px 12px;cursor:pointer;border-bottom:1px solid #f0f0f0;font-size:14px;';
                item.innerHTML = '<b>' + escHtml(addr.t) + '</b> › ' + escHtml(addr.a) + ' › ' + escHtml(addr.p) + ' <span style="color:#999;">' + escHtml(addr.z) + '</span>';
                item.addEventListener('mouseenter', function() { item.style.background = '#f0f9f0'; });
                item.addEventListener('mouseleave', function() { item.style.background = ''; });
                item.addEventListener('click', function() { selectAddress(addr); });
                resultsDiv.appendChild(item);
            });
            resultsDiv.style.display = 'block';
        }).catch(function() {
            resultsDiv.style.display = 'none';
        });
    }

    function selectAddress(addr) {
        resultsDiv.style.display = 'none';
        searchInput.value = '';
        selectedDiv.innerHTML = 'ตำบล<b>' + escHtml(addr.t) + '</b> อำเภอ<b>' + escHtml(addr.a) + '</b> จังหวัด<b>' + escHtml(addr.p) + '</b> <b>' + escHtml(addr.z) + '</b>'
            + ' <a href="#" style="color:#e74c3c;margin-left:8px;" onclick="this.closest(\'.addr-group\').querySelector(\'.addr-selected\').style.display=\'none\';this.closest(\'.addr-group\').querySelector(\'input[type=hidden]\').value=\'\';return false;">✕</a>';
        selectedDiv.style.display = 'block';
        updateHiddenValue(addr);
    }

    function updateHiddenValue(addr) {
        hiddenInput.value = JSON.stringify({
            house: houseInput.value.trim(),
            t: addr.t, a: addr.a, p: addr.p, z: addr.z
        });
    }

    // Update hidden value when house number changes
    houseInput.addEventListener('input', function() {
        if (hiddenInput.value) {
            try {
                var addr = JSON.parse(hiddenInput.value);
                addr.house = houseInput.value.trim();
                hiddenInput.value = JSON.stringify(addr);
            } catch(e) {}
        }
    });
}

// ── Submit ────────────────────────────────────────────────

async function submitDocument() {
    if (!currentTemplate) return;

    var fieldValues = {};
    var fields = currentTemplate.required_fields || [];
    var valid = true;
    fields.forEach(function(f) {
        var el = document.querySelector('[name="' + f.name + '"]');
        // Skip hidden conditional fields
        var fieldDiv = el ? el.closest('.liff-field') : null;
        if (fieldDiv && fieldDiv.style.display === 'none') return;

        var val = el ? el.value.trim() : '';
        if (f.required && !val) {
            valid = false;
            if (el) el.style.borderColor = '#e74c3c';
        } else if (el) {
            el.style.borderColor = '#dfe6e9';
        }
        fieldValues[f.name] = val;
    });

    if (!valid) return;

    var caseId = parseInt(document.getElementById('sel-case').value) || null;
    var isDocxTemplate = currentTemplate.is_docx_template || false;
    var templateName = currentTemplate.name || 'เอกสาร';

    // Show submitting state with appropriate message
    document.getElementById('submit-area').style.display = 'none';
    document.getElementById('dynamic-fields').style.display = 'none';
    document.getElementById('tmpl-field').style.display = 'none';
    document.getElementById('sel-category').closest('.liff-field').style.display = 'none';
    document.getElementById('case-field').style.display = 'none';
    document.getElementById('generating').style.display = 'block';

    // Set loading message based on template type
    var genMsg = document.getElementById('gen-msg');
    var genSub = document.getElementById('gen-sub');
    if (isDocxTemplate) {
        genMsg.textContent = 'กำลังสร้างเอกสาร...';
        genSub.textContent = 'สร้างจากแบบฟอร์ม รอสักครู่';
    } else {
        genMsg.textContent = 'AI กำลังสร้างเอกสาร...';
        genSub.textContent = 'อาจใช้เวลา 10-30 วินาที';
    }

    try {
        var result = await callApi('/liff/document/create/submit', {
            line_user_id: '',
            template_id: currentTemplate.id,
            field_values: fieldValues,
            lead_id: caseId,
        });

        if (result.error) {
            showError(result.message || 'เกิดข้อผิดพลาด');
            return;
        }

        // Poll until generation finishes
        var draftId = result.draft_id;
        var maxAttempts = 60;
        var lastStatus = null;
        for (var i = 0; i < maxAttempts; i++) {
            await new Promise(function(r) { setTimeout(r, 2000); });
            try {
                lastStatus = await callApi('/liff/document/draft/' + draftId + '/status', {});
                if (lastStatus.state !== 'generating') break;
            } catch(e) { break; }
        }

        // Hide loading
        document.getElementById('generating').style.display = 'none';

        // Check final state
        if (!lastStatus || lastStatus.state === 'generating') {
            showError('การสร้างเอกสารใช้เวลานานกว่าปกติ กรุณาตรวจสอบในรายการเอกสาร');
            return;
        }

        // Show success with download buttons
        showSuccess(draftId, lastStatus, templateName);

    } catch(e) {
        showError('เกิดข้อผิดพลาด: ' + e.message);
    }
}

function showSuccess(draftId, status, templateName) {
    var el = document.getElementById('submit-success');
    el.style.display = 'block';

    // Template name
    document.getElementById('success-tmpl-name').textContent = templateName;

    // Description
    var desc = document.getElementById('success-desc');
    if (status.has_docx) {
        desc.textContent = 'สร้างจากแบบฟอร์มสำเร็จ พร้อมดาวน์โหลด';
    } else {
        desc.textContent = 'AI สร้างเอกสารเรียบร้อย สามารถดูหรือดาวน์โหลดได้';
    }

    // Download links
    var baseUrl = '/liff/document/draft/' + draftId;
    document.getElementById('dl-pdf').href = baseUrl + '/download?format=pdf';
    document.getElementById('dl-docx').href = baseUrl + '/download?format=docx';
    document.getElementById('draft-link').href = baseUrl;
}

function showError(message) {
    document.getElementById('generating').style.display = 'none';
    var el = document.getElementById('submit-error');
    el.style.display = 'block';
    document.getElementById('error-msg').textContent = message;
}

// ── Helpers ───────────────────────────────────────────────

async function callApi(url, params) {
    var resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: params }),
    });
    var json = await resp.json();
    if (json.error) throw new Error(json.error.message || 'Server error');
    return json.result;
}

function escHtml(s) {
    if (!s) return '';
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function escAttr(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Init ──────────────────────────────────────────────────

(async function() {
    try {
        var result = await callApi('/liff/document/create/data', {
            line_user_id: '',
        });

        // Hide initial loading
        var initLoading = document.getElementById('init-loading');
        if (initLoading) initLoading.style.display = 'none';

        if (result.error) {
            document.getElementById('auth-error').style.display = 'block';
            document.getElementById('auth-error-msg').textContent = result.message || 'ไม่มีสิทธิ์เข้าถึง';
            return;
        }

        allTemplates = result.templates || [];
        allCases = result.cases || [];

        if (allCases.length > 0) {
            var caseSel = document.getElementById('sel-case');
            allCases.forEach(function(c) {
                caseSel.innerHTML += '<option value="' + c.id + '">' + escHtml(c.name) + ' (' + escHtml(c.partner_name) + ')</option>';
            });
        }

        document.getElementById('doc-main').style.display = 'block';

    } catch(e) {
        var initLoading = document.getElementById('init-loading');
        if (initLoading) initLoading.style.display = 'none';
        document.getElementById('auth-error').style.display = 'block';
        document.getElementById('auth-error-msg').textContent = 'โหลดข้อมูลไม่ได้: ' + e.message;
    }
})();
