# Orange Pi 5 Remote Power Control

Orange Pi 5のGPIOに接続したリレーをブラウザまたはHTTP APIから操作し、PCマザーボードの`PWR_SW`を短押し・長押しするための小さなFastAPIアプリです。

この構成ではUSB Keyboard、Mouse、HDMIキャプチャ配信は使用しません。

## 現在の配線

- リレーボード: ELEKIT LK-RB1
- 制御GPIO: `GPIO0_D5`（`/dev/gpiochip0` line 29）
- 制御論理: Active High
- LK-RB1電源: 5V（GPIOからリレー電源を取らない）
- Orange PiとLK-RB1のGNDを共通化
- マザーボード`PWR_SW`: LK-RB1の`C-M`（Normally Open）へ接続
- ケースのPowerボタン: リレー接点と並列接続

## 操作

- `Power`: 0.2秒押下。PCの起動またはOSの通常電源ボタン動作
- `Force Off`: 既定で8秒押下。応答しないPCの強制電源断

Force Offは未保存データやファイルシステムを破損する可能性があります。

## API

Power操作に必要な3本だけを公開します。

```text
GET  /api/v1/status
POST /api/v1/power/press
POST /api/v1/power/force-off
```

Swagger UI: `http://100.97.177.61:8000/docs`

通常のPower:

```bash
curl -X POST http://100.97.177.61:8000/api/v1/power/press
```

Force Off:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"confirmation":"FORCE_OFF"}' \
  http://100.97.177.61:8000/api/v1/power/force-off
```

## 設定

実機の`/etc/default/remote-kvm`:

```bash
REMOTE_KVM_HOST=100.97.177.61
REMOTE_KVM_PORT=8000
REMOTE_KVM_POWER_CHIP=/dev/gpiochip0
REMOTE_KVM_POWER_LINE=29
REMOTE_KVM_POWER_ACTIVE_LOW=false
REMOTE_KVM_FORCE_OFF_SECONDS=8
```

`REMOTE_KVM_FORCE_OFF_SECONDS`は4～15秒の範囲で設定できます。

API自体に認証機能はありません。Tailscale IPだけにbindし、Tailscale ACLでアクセス元を制限してください。

## セットアップ

```bash
cd /opt/remote-kvm
/root/.local/bin/uv sync --locked
/root/.local/bin/uv run python -m unittest discover -s tests -v
./scripts/install.sh
```

`install.sh`はsystemd unitを配置するためroot権限が必要です。以前のUSB HID Gadgetサービスが存在する場合は停止・削除します。

## 確認

```bash
systemctl status remote-kvm-api.service
curl http://100.97.177.61:8000/api/v1/status
grep -E 'gpio-29|remote-kvm-power' /sys/kernel/debug/gpio
```

待機中のGPIO表示は`out lo`になります。

## 開発・検証

```bash
cd /opt/remote-kvm
/root/.local/bin/uv run python -m compileall -q main.py src tests
/root/.local/bin/uv run python -m unittest discover -s tests -v
bash -n scripts/install.sh
systemd-analyze verify systemd/remote-kvm-api.service
git diff --check
```
