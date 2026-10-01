#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${REMOTE_KVM_PROJECT_DIR:-/opt/remote-kvm}"
UV_BIN="${UV_BIN:-/root/.local/bin/uv}"

if [[ "${EUID}" -ne 0 ]]; then
    echo "install.sh must run as root" >&2
    exit 1
fi

if [[ ! -x "${UV_BIN}" ]]; then
    echo "uv not found or not executable: ${UV_BIN}" >&2
    exit 1
fi

cd "${PROJECT_DIR}"
"${UV_BIN}" sync --locked

install -m 0644 systemd/remote-kvm-api.service /etc/systemd/system/remote-kvm-api.service

if [[ -x /usr/local/sbin/kvm-gadget ]]; then
    /usr/local/sbin/kvm-gadget stop || true
fi
systemctl disable --now kvm-gadget.service 2>/dev/null || true
rm -f /usr/local/sbin/kvm-gadget /etc/systemd/system/kvm-gadget.service

systemctl daemon-reload
systemctl enable remote-kvm-api.service
systemctl restart remote-kvm-api.service

systemctl --no-pager --full status remote-kvm-api.service
