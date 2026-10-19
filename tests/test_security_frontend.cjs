const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const root = path.resolve(__dirname, '..');
const sanitizerSource = fs.readFileSync(path.join(root, 'static/js/purify.min.js'), 'utf8');
const chatSource = fs.readFileSync(path.join(root, 'static/js/script.js'), 'utf8');

function chatWindow(answer, loadSanitizer = true) {
    const dom = new JSDOM(`<!doctype html><html><body>
        <button id="chat-icon"></button><div id="chat-popup"></div>
        <button id="close-chat-btn"></button><button id="send-chat-btn"></button>
        <input id="chat-input"><div id="chat-body"></div>
    </body></html>`, { url: 'http://127.0.0.1:5000', runScripts: 'outside-only' });
    const { window } = dom;
    window.fetch = async () => ({ ok: true, json: async () => ({ response: answer }) });
    if (loadSanitizer) window.eval(sanitizerSource);
    window.eval(chatSource);
    window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
    return dom;
}

test('user HTML is text and malicious Gemini HTML is stripped before insertion', async () => {
    const answer = '<p>Useful <strong>answer</strong></p><img src=x onerror="window.__attacked=true"><svg onload="window.__attacked=true"></svg><a href="javascript:window.__attacked=true">bad link</a>';
    const dom = chatWindow(answer);
    const { window } = dom;
    const userInput = '<img src=x onerror="window.__attacked=true">';
    window.document.getElementById('chat-input').value = userInput;
    window.document.getElementById('send-chat-btn').click();
    await new Promise(setImmediate);

    const userMessage = window.document.querySelector('.user-message');
    const botMessage = window.document.querySelectorAll('.bot-message')[0];
    assert.equal(userMessage.textContent, userInput);
    assert.equal(userMessage.querySelector('img'), null);
    assert.ok(botMessage.querySelector('strong'));
    assert.equal(botMessage.querySelector('img, svg, a, script'), null);
    assert.equal(botMessage.querySelector('[onerror], [onload], [href]'), null);
    assert.equal(window.__attacked, undefined);
    dom.window.close();
});

test('bot HTML falls back to inert text if sanitizer is unavailable', async () => {
    const answer = '<img src=x onerror="window.__attacked=true">';
    const dom = chatWindow(answer, false);
    const { window } = dom;
    window.document.getElementById('chat-input').value = 'question';
    window.document.getElementById('send-chat-btn').click();
    await new Promise(setImmediate);
    const botMessage = window.document.querySelector('.bot-message');
    assert.equal(botMessage.textContent, answer);
    assert.equal(botMessage.querySelector('img'), null);
    assert.equal(window.__attacked, undefined);
    dom.window.close();
});

test('admin delete form carries the CSRF token from the page', () => {
    const template = fs.readFileSync(path.join(root, 'templates/admin.html'), 'utf8');
    const script = template.match(/<script>([\s\S]*?)<\/script>/)[1];
    const dom = new JSDOM(`<!doctype html><html><body>
        <input id="file" type="file">
        <div id="file-info"></div>
        <form class="upload-form"><input name="csrf_token" value="test-csrf-token"></form>
        <button class="btn-delete-file" data-filename="document.txt"></button>
    </body></html>`, { url: 'http://127.0.0.1:5000', runScripts: 'outside-only' });
    const { window } = dom;
    window.confirm = () => true;
    let submitted = false;
    window.HTMLFormElement.prototype.submit = function () { submitted = true; };
    window.eval(script);
    window.document.querySelector('.btn-delete-file').click();

    const deleteForm = window.document.querySelector('form[action="/admin/delete/document.txt"]');
    assert.ok(deleteForm);
    assert.equal(deleteForm.querySelector('input[name="csrf_token"]').value, 'test-csrf-token');
    assert.equal(submitted, true);
    dom.window.close();
});
