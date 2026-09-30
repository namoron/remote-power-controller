import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "remote_kvm.app:app",
        host=os.getenv("REMOTE_KVM_HOST", "127.0.0.1"),
        port=int(os.getenv("REMOTE_KVM_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
