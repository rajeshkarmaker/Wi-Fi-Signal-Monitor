import subprocess
import re
import threading
import collections
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ── Config ────────────────────────────────────────────────────────────────────
MAX_POINTS     = 120    # number of data points shown on graph
UPDATE_MS      = 0    # graph redraw interval in ms (10 fps)
GOOD_THRESHOLD = -60    # dBm → green
FAIR_THRESHOLD = -75    # dBm → yellow | below → red

# ── Shared state (written by thread, read by graph) ───────────────────────────
rssi_history = collections.deque([None] * MAX_POINTS, maxlen=MAX_POINTS)
latest_rssi  = None
lock         = threading.Lock()
fill         = None

# ── Background thread — runs your exact while($true) loop ─────────────────────
def poll_rssi():
    global latest_rssi
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-Command",
         'while($true){(netsh wlan show interfaces) -match "Rssi"}'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
        errors="ignore",
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    for line in proc.stdout:          # blocks here, reads each line as it arrives
        m = re.search(r"Rssi\s*:\s*(-?\d+)", line, re.IGNORECASE)
        if m:
            with lock:
                latest_rssi = int(m.group(1))

thread = threading.Thread(target=poll_rssi, daemon=True)
thread.start()

# ── Colour helpers ────────────────────────────────────────────────────────────
def quality_color(dbm):
    if dbm is None:           return "#555555"
    if dbm >= GOOD_THRESHOLD: return "#39ff80"
    if dbm >= FAIR_THRESHOLD: return "#ffd166"
    return "#ef476f"

def quality_label(dbm):
    if dbm is None:           return "Waiting..."
    if dbm >= GOOD_THRESHOLD: return "Excellent"
    if dbm >= FAIR_THRESHOLD: return "Fair"
    return "Poor"

# ── Plot setup ────────────────────────────────────────────────────────────────
BG    = "#0d0f14"
PANEL = "#13161e"
GRID  = "#1e2130"
TEXT  = "#c8cde4"
ACCENT= "#6e8efb"

fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor(BG)
ax.set_facecolor(PANEL)

ax.axhspan(-50,   0,  alpha=0.06, color="#39ff80", zorder=0)
ax.axhspan(-75,  -50, alpha=0.06, color="#ffd166", zorder=0)
ax.axhspan(-100, -75, alpha=0.06, color="#ef476f", zorder=0)

for y, lbl, col in [(GOOD_THRESHOLD, "Good  -60 dBm", "#39ff80"),
                    (FAIR_THRESHOLD, "Fair  -75 dBm", "#ffd166")]:
    ax.axhline(y, color=col, linewidth=0.6, linestyle="--", alpha=0.5, zorder=1)
    ax.text(1, y + 1, lbl, color=col, fontsize=7, alpha=0.7,
            transform=ax.get_yaxis_transform())

ax.set_xlim(0, MAX_POINTS - 1)
ax.set_ylim(-100, -20)
ax.invert_xaxis()
ax.set_ylabel("Signal Strength (dBm)", color=TEXT, fontsize=10)
ax.set_xlabel(f"Last {MAX_POINTS} samples  (newest -> right)", color=TEXT, fontsize=9)
ax.tick_params(colors=TEXT, labelsize=8)
for sp in ax.spines.values():
    sp.set_edgecolor(GRID)
ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)

line,     = ax.plot([], [], color=ACCENT, linewidth=2, zorder=3)
dot,      = ax.plot([], [], "o", markersize=8,  zorder=5)
dot_glow, = ax.plot([], [], "o", markersize=14, alpha=0.25, zorder=4)

fig.text(0.5, 0.96, "Wi-Fi Signal Monitor",
         ha="center", color=TEXT, fontsize=14, fontweight="bold")
dbm_txt  = fig.text(0.13, 0.82, "- dBm", color=ACCENT,
                    fontsize=28, fontweight="bold")
qual_txt = fig.text(0.13, 0.74, "Waiting for data...", color="#555f7a", fontsize=11)
time_txt = fig.text(0.87, 0.82, "", ha="right", color="#555f7a", fontsize=8)

plt.tight_layout(rect=[0, 0, 1, 0.88])

# ── Animation — reads latest value from thread, appends to history ─────────────
def update(_frame):
    global fill

    with lock:
        dbm = latest_rssi

    rssi_history.append(dbm)

    ys = list(rssi_history)
    xs = list(range(MAX_POINTS - 1, -1, -1))  # [119 … 0], newest = 0

    valid = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if not valid:
        return

    vx, vy = zip(*valid)
    line.set_data(vx, vy)

    if fill is not None:
        fill.remove()
    fill = ax.fill_between(vx, vy, -100, alpha=0.12, color=ACCENT, zorder=2)

    latest_y = vy[-1]
    latest_x = vx[-1]
    col = quality_color(latest_y)

    dot.set_data([latest_x], [latest_y])
    dot.set_color(col)
    dot_glow.set_data([latest_x], [latest_y])
    dot_glow.set_color(col)

    dbm_txt.set_text(f"{latest_y} dBm")
    dbm_txt.set_color(col)
    qual_txt.set_text(quality_label(latest_y))
    qual_txt.set_color(col)
    time_txt.set_text(datetime.datetime.now().strftime("%H:%M:%S"))

    fig.canvas.draw_idle()

ani = animation.FuncAnimation(
    fig, update,
    interval=UPDATE_MS,
    blit=False,
    cache_frame_data=False
)

plt.show()
