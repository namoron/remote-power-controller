# Orange Pi 5 Remote KVM

Orange Pi 5 の USB-C Device mode を利用し、対象PCへ USB Keyboard / Mouse を提供するRemote KVMです。FastAPIからHID操作を受け付けます。GPIOリレーによる `PWR_SW` / `RESET_SW` とUSB HDMIキャプチャ配信は、バックエンドを交換して追加できる構成です。

## 現在できること

- ConfigFSでKeyboard (`/dev/hidg0`) とMouse (`/dev/hidg1`) を作成
- `fc000000.usb` をUDCとして使用
- systemdによるGadget/APIの自動起動
- Keyboardのキー＋modifier送信
- Mouseの移動、ホイール、左右中央クリック
- USB HDMIキャプチャのMJPEG配信と統合Web UI
- GPIO電源制御と映像配信の拡張インターフェース

現時点ではGPIOの実バックエンドと認証機能は未実装です。APIは安全のため初期値で `127.0.0.1:8000` のみに待ち受けます。

## 構成

```text
scripts/kvm-gadget              ConfigFS Gadgetの作成・削除・状態確認
scripts/install.sh              uv同期とsystemdへの配置
systemd/kvm-gadget.service      USB Gadget自動起動
systemd/remote-kvm-api.service  FastAPI自動起動
src/remote_kvm/app.py           API
src/remote_kvm/hid/             HIDレポート生成とデバイス書込み
src/remote_kvm/power/           GPIO電源制御の差し替え口
src/remote_kvm/video/           FFmpeg MJPEG配信と差し替え口
tests/                          実HIDへ書き込まない単体テスト
```

## 前提

- Orange Pi 5 / Ubuntu 22.04系
- `/sys/class/udc/fc000000.usb` が存在すること
- `/sys/kernel/debug/usb/fc000000.usb/mode` が利用できること
- Gitとuvが導入済みであること
- プロジェクト配置先は `/opt/remote-kvm`

この実機ではuvを `/root/.local/bin/uv` に配置しています。

## セットアップ

新規環境では、まずリポジトリを `/opt/remote-kvm` に配置します。

```bash
cd /opt/remote-kvm
/root/.local/bin/uv sync --locked
/root/.local/bin/uv run python -m unittest discover -s tests -v
```

次の操作は `/usr/local/sbin` と `/etc/systemd/system` を変更するためroot権限が必要です。

```bash
cd /opt/remote-kvm
./scripts/install.sh
```

個別に確認する場合:

```bash
systemctl status kvm-gadget.service remote-kvm-api.service
/opt/remote-kvm/scripts/kvm-gadget status
ls -l /dev/hidg0 /dev/hidg1
curl http://127.0.0.1:8000/api/v1/status
```

Orange Pi標準の `orangepi5-usb2-init.service` は起動時に同じコントローラをhostへ設定します。本プロジェクトはそのunitを変更せず、`kvm-gadget.service` を後から起動してdeviceへ切り替えます。

## APIへ安全にアクセスする

認証未実装なので、外部インターフェースへ直接公開しないでください。手元PCからSSHトンネルを作成します。

```bash
ssh -L 8000:127.0.0.1:8000 root@100.97.177.61
```

その接続を維持したまま、ブラウザで次を開きます。

- 操作画面: `http://127.0.0.1:8000/`
- APIドキュメント: `http://127.0.0.1:8000/docs`

操作画面の映像をクリックするとPointer Lockになり、Keyboardと相対Mouse操作が対象PCへ送られます。`Esc` でMouseを解放できます。

待受け先は任意の `/etc/default/remote-kvm` で上書きできますが、認証やFirewallを用意するまではlocalhostを推奨します。

```bash
REMOTE_KVM_HOST=127.0.0.1
REMOTE_KVM_PORT=8000
REMOTE_KVM_VIDEO_DEVICE=/dev/v4l/by-id/usb-MACROSILICON_USB_Video-video-index0
REMOTE_KVM_VIDEO_RESOLUTION=1280x720
REMOTE_KVM_VIDEO_FPS=30
```

変更後は `systemctl restart remote-kvm-api.service` を実行します。

## API例

状態確認:

```bash
curl http://127.0.0.1:8000/api/v1/status
```

`Ctrl+Alt+Delete` はDeleteキーへmodifierを付けて送信できます。

```bash
curl -X POST http://127.0.0.1:8000/api/v1/keyboard/press \
  -H 'content-type: application/json' \
  -d '{"key":"delete","modifiers":["left_ctrl","left_alt"]}'
```

Mouse移動と左クリック:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/mouse/move \
  -H 'content-type: application/json' \
  -d '{"dx":20,"dy":-10,"wheel":0}'

curl -X POST http://127.0.0.1:8000/api/v1/mouse/click \
  -H 'content-type: application/json' \
  -d '{"button":"left"}'
```

対象PCがUSB接続されていない場合、HID送信は `503` になることがあります。これは想定動作です。

## 再起動後の確認

リモート接続が復旧できることを確認してからOrange Piを再起動してください。

```bash
systemctl reboot
```

再接続後:

```bash
cat /sys/kernel/debug/usb/fc000000.usb/mode
systemctl is-active kvm-gadget.service remote-kvm-api.service
/opt/remote-kvm/scripts/kvm-gadget status
curl http://127.0.0.1:8000/api/v1/status
```

## 物理接続が必要な次の試験

ここから先は、データ通信対応の USB-C → USB-A ケーブルでOrange Piと対象PCを接続して行います。Orange Piは安定した別電源で給電し、電源経路や逆給電に問題がない構成を確認してください。

1. 対象PC側で `Remote KVM`、Keyboard、Mouseが列挙されることを確認する。
2. 対象PCで文字入力可能な画面を開く。
3. まず `a` など影響の小さいキーをAPIから1回送る。
4. Mouseを小さく移動し、左右方向と上下方向を確認する。
5. 左クリックを確認する。
6. 対象PC再起動後のBIOS/UEFI画面でもKeyboard/Mouseが使えるか確認する。

この試験までは、重要データを開いていないテスト用PCで行ってください。

## GPIOリレー追加方針

`src/remote_kvm/power/base.py` の `PowerController` を実装し、`create_app()` へ注入します。実装時は以下を守ります。

- マザーボードの `PWR_SW` / `RESET_SW` には外部電圧を印加しない。
- 無電圧接点のリレーまたは適切に絶縁された回路を使う。
- ケースの物理スイッチとNormally Open接点を並列接続する。
- 起動時に誤作動しないGPIO状態を選び、通常操作は短いパルスにする。
- 長押し電源断は通常のPower操作とは別APIにし、明示的な安全策を置く。

GPIO番号はOrange Piの物理ピン番号・SoC line offset・利用ライブラリで表記が異なるため、配線確定後に実機の `gpioinfo` と回路を照合して決めます。

## HDMIキャプチャ

`v4l2-ctl --list-devices` と対応フォーマットを確認し、USBキャプチャ固有のby-idパスを使用します。SoC内蔵codec/camera用video nodeを番号だけで決め打ちしないでください。

現在はキャプチャが生成するMJPEGをFFmpegで再圧縮せず、FastAPIのmultipart streamとして配信します。同時viewerは1接続です。カラーバーだけが表示される場合、キャプチャ自体は動作していますがHDMI入力信号がありません。対象PCの電源、出力先、HDMIケーブルを確認してください。

将来さらに低遅延化または複数viewerが必要なら、`VideoProvider` をWebRTCまたは専用streaming daemonへ差し替えます。

## 開発・検証

```bash
cd /opt/remote-kvm
/root/.local/bin/uv sync --locked
/root/.local/bin/uv run python -m compileall -q main.py src tests
/root/.local/bin/uv run python -m unittest discover -s tests -v
bash -n scripts/kvm-gadget scripts/install.sh
systemd-analyze verify systemd/*.service
git diff --check
```
