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
    .panel { width: min(100%, 32rem); padding: 2rem; border-radius: .8rem; background: #1b1f28; box-shadow: 0 8px 36px #000a; }
    .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem; }
    button { color: inherit; background: #303746; border: 1px solid #4b5568; border-radius: .5rem; padding: 1.2rem .7rem; font-size: 1rem; cursor: pointer; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    #force { background: #5e2028; border-color: #9b3a46; }
    .note { color: #aeb6c6; line-height: 1.6; }
  </style>
</head>
<body>
  <header>
    <strong>Orange Pi Remote KVM</strong>
    <span id="status">接続確認中</span>
  </header>
  <main>
    <div class="panel">
      <h1>Power Control</h1>
      <p class="note">Powerは0.2秒押下、Force Offは5秒間押下します。Force OffはOSを介さず電源を切るため、データを失う可能性があります。</p>
      <div class="actions">
        <button id="power" disabled>Power</button>
        <button id="force" disabled>Force Off</button>
      </div>
    </div>
  </main>
  <script>
    const statusNode = document.querySelector('#status');
    const powerButton = document.querySelector('#power');
    const forceButton = document.querySelector('#force');
    const post = (path, body) => fetch(path, {
      method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify(body)
    }).then(async response => {
      if (!response.ok) throw new Error((await response.json()).detail || response.statusText);
      return response.json();
    }).catch(error => { statusNode.textContent = error.message; throw error; });

    async function refreshStatus() {
      try {
        const data = await fetch('/api/v1/status').then(response => response.json());
        const ready = data.power.available;
        powerButton.disabled = !ready || data.power.busy;
        forceButton.disabled = !ready || data.power.busy;
        statusNode.textContent = ready ? (data.power.busy ? '操作中' : 'Power ready') : 'リレー未設定';
      } catch { statusNode.textContent = 'API接続失敗'; }
    }
    refreshStatus(); setInterval(refreshStatus, 5000);

    powerButton.addEventListener('click', async () => {
      if (!confirm('Powerボタンを短押しします。実行しますか？')) return;
      powerButton.disabled = forceButton.disabled = true;
      await post('/api/v1/power/press', {});
      setTimeout(refreshStatus, 300);
    });
    forceButton.addEventListener('click', async () => {
      const answer = prompt('強制電源OFFを実行します。FORCE と入力してください。');
      if (answer !== 'FORCE') return;
      powerButton.disabled = forceButton.disabled = true;
      statusNode.textContent = '5秒間押下中';
      await post('/api/v1/power/force-off', {confirmation:'FORCE_OFF'});
      setTimeout(refreshStatus, 300);
    });
  </script>
</body>
</html>
"""
