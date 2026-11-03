# 📶 Wi-Fi Signal Monitor

A real-time Wi-Fi signal strength graph for Windows. Walk around, rotate your laptop, or move between rooms and watch your signal (in dBm) change live.

> **Note:** This project was generated with the help of [Claude](https://claude.ai) (Anthropic). I'm using it as a learning project in Python, threading and data visualization.

## Features
- Live line graph of the last 120 signal readings
- Color-coded quality: 🟢 Excellent (≥ -60 dBm), 🟡 Fair (≥ -75 dBm), 🔴 Poor
- Current dBm value and quality label displayed on screen
- Dark-themed matplotlib interface

## How it works
1. A background thread runs `netsh wlan show interfaces` through PowerShell in a loop.
2. A regex extracts the `Rssi` value (in dBm) from the output.
3. matplotlib's `FuncAnimation` reads the latest value and redraws the graph.

## Requirements
- **Windows** (uses `netsh` and PowerShell)
- Python 3.8+
- A Wi-Fi adapter whose `netsh wlan show interfaces` output includes `Rssi`

## Installation & usage
```bash
git clone https://github.com/rajeshkarmaker/Wi-Fi-Signal-Monitor.git
cd Wi-Fi-Signal-Monitor
pip install -r requirements.txt
python "Wi-Fi Signal Monitor.py"
```

## Reading the graph
| dBm | Quality |
|---|---|
| -60 or higher | Excellent |
| -60 to -75 | Fair |
| below -75 | Poor |

Closer to 0 is stronger (e.g. -45 dBm is better than -80 dBm).

## Configuration
Edit the constants at the top of `wifi_monitor.py`:
- `MAX_POINTS`: number of samples shown
- `UPDATE_MS`: graph refresh interval (ms)
- `GOOD_THRESHOLD` / `FAIR_THRESHOLD`: color thresholds

## Troubleshooting
- **Graph stays on "Waiting for data":** your adapter may not report `Rssi`. Run `netsh wlan show interfaces` in PowerShell and check which fields appear.
- **No window / errors on Mac or Linux:** this tool is Windows-only.

## License
MIT. See [LICENSE](LICENSE).