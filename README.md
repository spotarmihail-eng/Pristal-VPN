# Pristal VPN

**Pristal VPN** is an experimental, free proxy manager for Windows 10/11. It fetches public HTTP and SOCKS5 proxy lists, checks whether their TCP ports accept connections, and can launch a selected proxy through [sing-box](https://github.com/SagerNet/sing-box).

> **Important:** This first release is a proxy manager, not a full VPN. It configures the Windows system HTTP proxy. Only applications that honor the Windows proxy setting will use it; many games, UDP traffic, and some apps will bypass it.

## Features

- Russian-language desktop interface.
- Fetches public HTTP and SOCKS5 proxy lists from community-maintained GitHub lists.
- Sorts candidates by TCP connection time.
- Starts a selected proxy using sing-box.
- Configures Windows system proxy to `127.0.0.1:2080` and restores the previous settings when stopped normally.
- Exports the discovered list to CSV.

## Download for Windows

Open the repository's **Actions → Build Windows EXE** workflow, run it with **Run workflow**, and download the `PristalVPN-Windows-x64` artifact. The ZIP contains both required files:

- `PristalVPN.exe`
- `sing-box.exe`

Extract both files into the same folder, then run `PristalVPN.exe`. The build workflow downloads the latest stable official Windows AMD64 sing-box release automatically.

## Run from source

1. Download or clone this repository.
2. Install Python 3.10+ from [python.org](https://www.python.org/downloads/windows/).
3. Download the Windows AMD64 sing-box release from the [official sing-box releases](https://github.com/SagerNet/sing-box/releases).
4. Extract `sing-box.exe` into the same folder as `PristalVPN.py`.
5. Double-click `run.bat` or run `py -3 PristalVPN.py` in Command Prompt.

## Build locally

Open PowerShell in the project folder:

```powershell
py -m pip install pyinstaller
py -m PyInstaller --onefile --windowed --name PristalVPN PristalVPN.py
```

Copy the official Windows AMD64 `sing-box.exe` beside `dist\\PristalVPN.exe`. The app looks for the engine beside the executable when packaged.

## Security and limitations

- Public proxies are operated by unknown third parties. They may log connection metadata, be unreliable, or intercept unencrypted traffic. Do not use public proxies for banking, payments, passwords, or sensitive accounts.
- A successful TCP connection test does **not** verify that the proxy protocol works, that it is private, or that it is safe.
- The displayed latency is the TCP connection time to the proxy endpoint, not game ping or end-to-end latency.
- The app does not provide a TUN interface, a kill switch, DNS leak protection, or guaranteed routing for every application.
- Proxy lists are external community resources and can change or disappear.

## Third-party components and data sources

- [sing-box](https://github.com/SagerNet/sing-box) — proxy engine. The Windows build workflow downloads its official release; see the upstream project for its license and notices.
- [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List) — community-maintained public proxy lists.

Review third-party licenses and notices before redistributing binaries.

## Contributing

Issues and pull requests are welcome. Please report reproducible bugs without posting credentials, private proxy secrets, or personal information.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
