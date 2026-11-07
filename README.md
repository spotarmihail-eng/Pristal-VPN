# Pristal VPN

**Pristal VPN** is an experimental, free proxy manager for Windows 10/11. It fetches public HTTP and SOCKS5 proxy lists, checks whether their TCP ports accept connections, and can launch a selected proxy through the bundled [sing-box](https://github.com/SagerNet/sing-box) engine.

> **Important:** This is a proxy manager, not a full VPN. It configures the Windows system HTTP proxy. Only applications that honor that setting will use it; many games, UDP traffic, and some apps may bypass it.

## Features

- Russian-language desktop interface.
- Fetches public HTTP/SOCKS5 proxy lists from community-maintained sources.
- Sorts candidates by TCP connection time.
- Runs a selected proxy through the bundled sing-box engine.
- Configures Windows system proxy to `127.0.0.1:2080` and restores previous settings when stopped normally.
- Exports discovered proxies to CSV.

## Download for Windows

Open **Actions → Build Windows EXE** in this repository and download the successful run's `PristalVPN-Windows-x64` artifact. It contains a single file: `PristalVPN.exe`.

**You do not need to download or place `sing-box.exe` separately.** GitHub Actions downloads the official stable Windows AMD64 sing-box release and embeds it into PristalVPN.exe. At runtime, PyInstaller extracts the bundled engine into its temporary application directory.

## Run from source

When running `PristalVPN.py` directly (not the packaged EXE), place the official Windows AMD64 `sing-box.exe` beside the Python source file.

## Build locally

```powershell
py -m pip install pyinstaller
py -m PyInstaller --onefile --windowed --name PristalVPN --add-binary "vendor/sing-box.exe;." PristalVPN.py
```

Place the official Windows AMD64 sing-box executable at `vendor\\sing-box.exe` before building.

## Security and limitations

- Public proxies are operated by unknown third parties. They may log metadata, be unreliable, or intercept unencrypted traffic. Do not use public proxies for banking, payments, passwords, or sensitive accounts.
- A successful TCP connection test does **not** verify that the proxy protocol works, that the server is private, or that it is safe.
- The displayed latency is the TCP connection time to the proxy endpoint, not game ping or end-to-end latency.
- This version does not provide a TUN interface, kill switch, or DNS leak protection.
- Proxy lists are external community resources and can change or disappear.

## Third-party components

- [sing-box](https://github.com/SagerNet/sing-box) — networking engine bundled into the Windows build. See the upstream project for its license and notices.
- [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List) — public proxy lists.

Review and include required third-party license notices when redistributing the application.

## License

MIT. See [LICENSE](LICENSE).
