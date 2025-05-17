# InfoCenter 🖥️

A minimal macOS menu bar app built with Python and [rumps](https://github.com/jaredks/rumps) that displays system information such as CPU usage, memory, storage, battery, clipboard, IP addresses, and more — directly in the menu bar.

---

## Features

- ⚡ CPU, memory, storage, and battery, uptime stats
- 📋 Clipboard history
- 🌐 IP address display & Network speed
- 💾 Menu bar only
- 🛠️ Lightweight and easily configurable


## TODO

  - Make clipboard history copy the selected text
  - Dark mode toggle
  - Memory usage by actual GB instead of percentage

---

## 📦 Installation

> Note: This app is macOS-only and uses Python3.

### 1. Clone the repository
```bash
git clone https://github.com/aariir/infoCenter.git
cd infoCenter
```

### 2. Build using py2app
```bash
python3 setup.py py2app
```
The output will be in the /dist directory.

---

## 🧾 License
This project is licensed under the MIT License.
Feel free to fork, modify, and share!
