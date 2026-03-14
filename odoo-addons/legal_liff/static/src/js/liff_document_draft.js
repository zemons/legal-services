/**
 * LIFF Document Draft Page
 */

function copyContent() {
    var el = document.getElementById('doc-content');
    var text = el.textContent || el.innerText;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            alert('คัดลอกเรียบร้อย');
        });
    } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        alert('คัดลอกเรียบร้อย');
    }
}

function getDraftId() {
    var m = window.location.pathname.match(/\/liff\/document\/draft\/(\d+)/);
    return m ? parseInt(m[1]) : 0;
}

function doAction(action, extra) {
    var id = getDraftId();
    if (!id) return;
    var params = {action: action};
    if (extra) {
        for (var k in extra) params[k] = extra[k];
    }
    fetch('/liff/document/draft/' + id + '/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: params})
    })
    .then(function(r) { return r.json(); })
    .then(function(j) {
        var res = j.result || {};
        if (res.success) {
            alert(res.message || 'สำเร็จ');
            window.location.reload();
        } else {
            alert(res.error || 'เกิดข้อผิดพลาด');
        }
    })
    .catch(function(e) {
        alert('เกิดข้อผิดพลาด: ' + e);
    });
}

function showRevisionForm() {
    document.getElementById('revision-form').style.display = 'block';
    document.getElementById('revision-notes').focus();
}

function submitRevision() {
    var notes = document.getElementById('revision-notes').value.trim();
    if (!notes) {
        alert('กรุณาระบุสิ่งที่ต้องการแก้ไข');
        return;
    }
    doAction('request_revision', {notes: notes});
}
