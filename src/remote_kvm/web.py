CONTROL_PAGE = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Orange Pi Remote KVM</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #111318; color: #e8eaf0; }
    header { display: flex; gap: 1rem; align-items: center; padding: .7rem 1rem; background: #1b1f28; }
    header strong { margin-right: auto; }
    #status { color: #8bd5a6; font-size: .9rem; }
    main { display: grid; place-items: center; min-height: calc(100vh - 54px); padding: 1rem; }
    .screen { position: relative; width: min(100%, 1280px); background: #000; box-shadow: 0 8px 36px #000a; }
    #video { display: block; width: 100%; aspect-ratio: 16/9; object-fit: contain; cursor: crosshair; }
    .hint { position: absolute; left: .7rem; bottom: .7rem; padding: .4rem .6rem; border-radius: .35rem; background: #000a; font-size: .8rem; pointer-events: none; }
    button { color: inherit; background: #303746; border: 1px solid #4b5568; border-radius: .35rem; padding: .4rem .7rem; }
  </style>
</head>
<body>
  <header>
    <strong>Orange Pi Remote KVM</strong>
    <span id="status">接続確認中</span>
    <button id="cad">Ctrl+Alt+Delete</button>
    <button id="release">Mouse解放</button>
  </header>
  <main>
    <div class="screen">
      <img id="video" src="/api/v1/video/stream.mjpg" alt="HDMI capture">
      <div class="hint">映像をクリックするとKeyboard/Mouse操作を開始（EscでMouse解放）</div>
    </div>
  </main>
  <script>
    const video = document.querySelector('#video');
    const statusNode = document.querySelector('#status');
    const specialKeys = {
      'Enter':'enter','Escape':'escape','Backspace':'backspace','Tab':'tab',' ':'space',
      'Delete':'delete','Insert':'insert','Home':'home','End':'end','PageUp':'page_up',
      'PageDown':'page_down','ArrowUp':'up','ArrowDown':'down','ArrowLeft':'left',
      'ArrowRight':'right'
    };
    const post = (path, body) => fetch(path, {
      method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify(body)
    }).then(async response => {
      if (!response.ok) throw new Error((await response.json()).detail || response.statusText);
      return response.json();
    }).catch(error => { statusNode.textContent = error.message; throw error; });

    async function refreshStatus() {
      try {
        const data = await fetch('/api/v1/status').then(response => response.json());
        statusNode.textContent = data.video.available && data.hid.keyboard_available
          ? 'HID / Video ready' : '一部デバイス未接続';
      } catch { statusNode.textContent = 'API接続失敗'; }
    }
    refreshStatus(); setInterval(refreshStatus, 5000);

    video.addEventListener('click', () => video.requestPointerLock());
    document.querySelector('#release').addEventListener('click', () => document.exitPointerLock());
    document.querySelector('#cad').addEventListener('click', () =>
      post('/api/v1/keyboard/press', {key:'delete', modifiers:['left_ctrl','left_alt']}));

    document.addEventListener('keydown', event => {
      if (event.repeat || ['Control','Shift','Alt','Meta'].includes(event.key)) return;
      let key = specialKeys[event.key] || event.key.toLowerCase();
      if (!/^[a-z0-9]$/.test(key) && !Object.values(specialKeys).includes(key) && !/^f([1-9]|1[0-2])$/.test(key)) return;
      event.preventDefault();
      const modifiers = [];
      if (event.ctrlKey) modifiers.push('left_ctrl');
      if (event.shiftKey) modifiers.push('left_shift');
      if (event.altKey) modifiers.push('left_alt');
      if (event.metaKey) modifiers.push('left_meta');
      post('/api/v1/keyboard/press', {key, modifiers});
    });

    let dx = 0, dy = 0, scheduled = false;
    document.addEventListener('mousemove', event => {
      if (document.pointerLockElement !== video) return;
      dx += event.movementX; dy += event.movementY;
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(() => {
        const sendX = Math.max(-127, Math.min(127, dx));
        const sendY = Math.max(-127, Math.min(127, dy));
        dx -= sendX; dy -= sendY; scheduled = false;
        if (sendX || sendY) post('/api/v1/mouse/move', {dx:sendX, dy:sendY, wheel:0});
      });
    });
    video.addEventListener('contextmenu', event => event.preventDefault());
    video.addEventListener('mousedown', event => {
      if (document.pointerLockElement !== video) return;
      event.preventDefault();
      const button = ['left','middle','right'][event.button];
      if (button) post('/api/v1/mouse/click', {button});
    });
    video.addEventListener('wheel', event => {
      if (document.pointerLockElement !== video) return;
      event.preventDefault();
      post('/api/v1/mouse/move', {dx:0, dy:0, wheel:event.deltaY > 0 ? -1 : 1});
    }, {passive:false});
  </script>
</body>
</html>
"""
