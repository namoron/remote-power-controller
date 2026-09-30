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

install -m 0755 scripts/kvm-gadget /usr/local/sbin/kvm-gadget
install -m 0644 systemd/kvm-gadget.service /etc/systemd/system/kvm-gadget.service
install -m 0644 systemd/remote-kvm-api.service /etc/systemd/system/remote-kvm-api.service

systemctl daemon-reload
systemctl enable kvm-gadget.service remote-kvm-api.service
systemctl restart kvm-gadget.service
systemctl restart remote-kvm-api.service

systemctl --no-pager --full status kvm-gadget.service remote-kvm-api.service
