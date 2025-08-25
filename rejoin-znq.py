# -*- coding: utf-8 -*-
import os
import time
import subprocess
import json
import ssl
import shutil
import platform
import urllib.request

# ====================== CẤU HÌNH CƠ BẢN ======================

APPLICATIONS = {
    '1. Roblox (Chính)': 'com.roblox.client',
}

CONFIG_FILE = 'roblox_config.json'
BRAND = "© ZNQ"  # footer trên Discord & banner

# UI: sau khi chọn hẹn giờ -> xóa màn hình & vẽ dashboard ngay
UI_CLEAR_AFTER_TIMER = True

# Bật Focus Mode khi start chức năng 1: đóng mọi app user trừ whitelist
FOCUS_MODE_ON_START = True
TERMUX_WHITELIST = ["com.termux", "com.termux.api"]

# ====================== ROOT-PRO TWEAKS (1,2,4,7) ======================

ROOT_TWEAKS = {
    "doze_killer": True,         # (1) Tắt Doze, whitelist deviceidle, stay-awake
    "priority_boost": True,      # (2) renice/ionice/taskset cho PID Roblox
    "appops_whitelist": True,    # (7) appops RUN_IN_BACKGROUND/WAKE_LOCK allow
    "restore_on_exit": False     # khôi phục stay-awake khi thoát (không bật mặc định)
}

# ====================== TIỆN ÍCH CHUNG =======================

def check_psutil():
    try:
        import psutil  # noqa
        return True
    except Exception:
        print("\n❌ Thiếu thư viện 'psutil'. Cài nhanh:  pip install psutil")
        return False

def term_width(default=80):
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default

def center_line(s: str, fill=' '):
    w = term_width()
    try:
        return s.center(w, fill) if fill and fill != ' ' else s.center(w)
    except Exception:
        return s

def print_big_znq():
    """Banner 'ZNQ' lớn, căn giữa (ASCII)."""
    Z = ["██████","     █","    █ ","   █  ","  █   "," █    ","██████"]
    N = ["█   █ ","██  █ ","█ █ █ ","█  ██ ","█   █ ","█   █ ","█   █ "]
    Q = [" ████ ","█    █","█    █","█    █","█ ██ █","█  ███"," ███ █"]
    combo = [f"{Z[i]}   {N[i]}   {Q[i]}" for i in range(len(Z))]
    print()
    for line in combo:
        print("\033[95m" + center_line(line) + "\033[0m")
    print(center_line("== ZNQ HACK MENU ==", ' '))
    print(center_line("-" * 26))

def get_packages_from_user_input():
    print("\nDán danh sách package (mỗi dòng 1 tên) → Enter dòng trống để kết thúc:")
    all_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        all_lines.append(line.strip())
    full_text = " ".join(all_lines)
    return [pkg for pkg in full_text.split() if pkg]

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"\n❌ Lỗi khi lưu cấu hình: {e}")
        return False

def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            return None
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"\n❌ Lỗi khi tải cấu hình: {e}")
        return None

def human_time(ts=None):
    if ts is None: ts = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

def iso8601_now():
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

def ensure_root_note():
    print("⚠️ Một số thao tác (xóa cache, doze/appops) cần quyền root.")
    print("   Gợi ý: cài 'tsu' và chạy: tsu -c 'python 1.py'")

def is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False

def get_device_name():
    name = os.popen("getprop ro.product.model 2>/dev/null").read().strip()
    if not name:
        brand = os.popen("getprop ro.product.brand 2>/dev/null").read().strip()
        model = os.popen("getprop ro.product.name 2>/dev/null").read().strip()
        name = (brand + " " + model).strip()
    if not name:
        name = platform.node() or "Android"
    return name

def fmt_gb(b):
    try:
        return f"{(float(b)/(1024**3)):.2f} GB"
    except Exception:
        return "N/A"

def has_bin(name: str) -> bool:
    return shutil.which(name) is not None

def run_quiet(cmd_list):
    try:
        subprocess.run(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
        return 0
    except Exception:
        try:
            os.system(" ".join(cmd_list) + " >/dev/null 2>&1")
        except Exception:
            pass
        return 1

def _as_float_pct(s, default=0.0):
    try:
        return float(str(s).replace('%','').strip())
    except Exception:
        return float(default)

def _hms(sec):
    sec = int(max(0, sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}h{m:02d}m{s:02d}s"

# ===== Helpers migrate config cũ → mới =====
def _normalize_packages(val):
    # Nhận cả list hoặc string "a, b  c\nd"
    if isinstance(val, list):
        return [p.strip() for p in val if isinstance(p, str) and p.strip()]
    if isinstance(val, str):
        tmp = val.replace('\n', ' ').replace('\t', ' ')
        for ch in [',', ';', '|']:
            tmp = tmp.replace(ch, ' ')
        return [p.strip() for p in tmp.split(' ') if p.strip()]
    return []

def _digits_only(s):
    s = str(s or '').strip()
    d = ''.join(ch for ch in s if ch.isdigit())
    return d or s

# ====================== DISCORD WEBHOOK ======================

def _send_http_payload(webhook_url: str, payload: dict, timeout: int = 10):
    try:
        if not webhook_url or not webhook_url.startswith("https://"):
            return False, "Webhook phải là https://discord.com/..."

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "curl/8.5.0",
            "Accept": "*/*",
        }

        ctx = None
        try:
            import certifi  # type: ignore
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = None

        try:
            req = urllib.request.Request(webhook_url, data=data, headers=headers, method="POST")
            if ctx is not None:
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                    code = getattr(resp, "status", resp.getcode()); _ = resp.read()
            else:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    code = getattr(resp, "status", resp.getcode()); _ = resp.read()
            if 200 <= code < 300:
                return True, "OK"
            return False, f"HTTP {code}"
        except Exception as e_url:
            if shutil.which("curl"):
                try:
                    cmd = [
                        "curl", "-sS", "-f", "--connect-timeout", "7", "--max-time", "10",
                        "-H", "Content-Type: application/json",
                        "-H", "User-Agent: curl/8.5.0",
                        "-X", "POST",
                        "-d", json.dumps(payload),
                        webhook_url
                    ]
                    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
                    if r.returncode == 0:
                        return True, "OK(curl)"
                    return False, f"curl exit {r.returncode}: {r.stderr.decode('utf-8','ignore')[:120]}"
                except Exception as e_curl:
                    return False, f"urlopen: {e_url} | curl: {e_curl}"
            return False, f"urlopen: {e_url}"
    except Exception as e:
        return False, str(e)

def post_discord(webhook_url: str, content: str, timeout: int = 10):
    return _send_http_payload(webhook_url, {"content": (content or "")[:1800]}, timeout)

def send_discord_embed(webhook_url: str, embed: dict, content: str = None, timeout: int = 10):
    payload = {"embeds": [embed]}
    if content:
        payload["content"] = content[:1800]
    return _send_http_payload(webhook_url, payload, timeout)

# ====================== THU THẬP CHỈ SỐ =====================

def pkg_running(pkg: str) -> bool:
    try:
        out = subprocess.check_output(["pidof", pkg], stderr=subprocess.STDOUT, text=True).strip()
        return bool(out)
    except Exception:
        return os.system(f'pgrep -f "{pkg}" >/dev/null 2>&1') == 0

def collect_system_status(pkgs):
    try:
        import psutil
    except Exception:
        psutil = None

    cpu = "N/A"; ram_pct = "N/A"; ram_avail = "N/A"; ram_total = "N/A"; uptime = "N/A"
    if psutil:
        try: cpu = f"{psutil.cpu_percent(interval=0):.1f}%"
        except Exception: pass
        try:
            vm = psutil.virtual_memory()
            ram_pct = f"{vm.percent:.1f}%"
            ram_avail = fmt_gb(vm.available)
            ram_total = fmt_gb(vm.total)
        except Exception: pass
        try:
            boot = getattr(psutil, "boot_time", lambda: None)()
            if boot:
                s = int(time.time() - boot); uptime = _hms(s)
        except Exception: pass

    battery = "N/A"
    try:
        if psutil and hasattr(psutil, "sensors_battery"):
            b = psutil.sensors_battery()
            if b is not None and b.percent is not None: battery = f"{int(b.percent)}%"
        if battery == "N/A":
            out = os.popen("dumpsys battery 2>/dev/null").read()
            for line in out.splitlines():
                t = line.strip().lower()
                if t.startswith("level:"):
                    battery = f"{int(t.split(':',1)[1].strip())}%"; break
    except Exception:
        pass

    running = sum(1 for p in pkgs if pkg_running(p))

    return {
        "cpu": cpu,
        "ram_pct": ram_pct,
        "ram_avail": ram_avail,
        "ram_total": ram_total,
        "battery": battery,
        "uptime": uptime,
        "running": running,
        "total": len(pkgs)
    }

# ====================== EMBED BUILDER ========================

def make_status_embed(title, place_id, pkgs, met, color=0x3498db, note=None):
    fields = [
        {"name": "◆ Device Name", "value": f"{get_device_name()}", "inline": True},
        {"name": "⚙️ CPU Usage", "value": f"{met['cpu']}", "inline": True},
        {"name": "🧠 Memory Usage", "value": f"{met['ram_pct']}", "inline": True},
        {"name": "💾 Memory Available", "value": f"{met['ram_avail']}", "inline": True},
        {"name": "💡 Total Memory", "value": f"{met['ram_total']}", "inline": True},
        {"name": "🔋 Battery", "value": f"{met['battery']}", "inline": True},
        {"name": "⏱ Uptime", "value": f"{met['uptime']}", "inline": True},
        {"name": "🎮 PlaceID", "value": str(place_id), "inline": True},
        {"name": "📦 Packages", "value": f"{met['running']}/{met['total']} running", "inline": True},
        {"name": "🔖 Tool", "value": "ĐANG HOẠT ĐỘNG ✅", "inline": True},
    ]
    desc = None
    if pkgs:
        preview = ", ".join(pkgs[:3])
        if len(pkgs) > 3: preview += f", +{len(pkgs)-3} nữa"
        desc = f"**Packages**: {preview}"
    if note:
        desc = (desc + "\n" if desc else "") + note

    return {
        "title": title,
        "description": desc,
        "color": color,
        "timestamp": iso8601_now(),
        "footer": {"text": BRAND},
        "fields": fields
    }

def make_autoclear_embed(place_id, pkgs, met, cleared_lines):
    body = "\n".join([f"✅ {x}" for x in cleared_lines][:20]) or "Không có mục nào."
    note = f"**Auto Clear Cache**\n{body}"
    return make_status_embed("🧹 Auto Clear Cache", place_id, pkgs, met, color=0xf1c40f, note=note)

def make_start_embed(place_id, pkgs, met):
    return make_status_embed("🟢 Bắt đầu giám sát", place_id, pkgs, met, color=0x2ecc71)

def make_heartbeat_embed(place_id, pkgs, met):
    return make_status_embed("💓 Heartbeat", place_id, pkgs, met, color=0x9b59b6)

def make_stop_embed(place_id, pkgs, met):
    e = make_status_embed("🔴 Dừng giám sát", place_id, pkgs, met, color=0xe74c3c)
    for f in e["fields"]:
        if f["name"].startswith("🔖 Tool"):
            f["value"] = "ĐÃ DỪNG ⛔"; break
    return e

def make_focus_embed(place_id, pkgs, met, closed_count):
    note = f"**Focus Mode**: Đã đóng {closed_count} ứng dụng người dùng để giải phóng tài nguyên."
    return make_status_embed("🚫 Focus Mode", place_id, pkgs, met, color=0xe67e22, note=note)

def make_root_embed(place_id, pkgs, met, note):
    return make_status_embed("🛡️ Root Optimizations", place_id, pkgs, met, color=0x1abc9c, note=note)

def make_kill_embed(place_id, pkgs, met, minutes, processed_lines):
    body = "\n".join([f"🔁 {x}" for x in processed_lines][:20]) or "Không có mục nào."
    note = f"**Kill theo lịch**: mỗi {minutes} phút\n{body}"
    return make_status_embed("♻️ Kill & Rejoin theo lịch", place_id, pkgs, met, color=0x00bcd4, note=note)

# ====================== ROOT HELPERS (1,2,7) ======================

def doze_killer_setup(packages):
    if not is_root():
        ensure_root_note(); return
    run_quiet(["dumpsys", "deviceidle", "disable"])
    run_quiet(["cmd", "deviceidle", "disable"])
    run_quiet(["settings", "put", "global", "stay_on_while_plugged_in", "3"])
    run_quiet(["svc", "power", "stayon", "true"])
    targets = set(packages) | set(TERMUX_WHITELIST)
    for pkg in targets:
        run_quiet(["cmd", "deviceidle", "whitelist", f"+{pkg}"])
        if ROOT_TWEAKS.get("appops_whitelist", True):
            run_quiet(["cmd", "appops", "set", pkg, "RUN_IN_BACKGROUND", "allow"])
            run_quiet(["cmd", "appops", "set", pkg, "WAKE_LOCK", "allow"])

def doze_killer_teardown(packages):
    if not is_root():
        return
    if ROOT_TWEAKS.get("restore_on_exit", False):
        run_quiet(["svc", "power", "stayon", "false"])
        run_quiet(["settings", "put", "global", "stay_on_while_plugged_in", "0"])

def boost_pkg_priority(pkg):
    if not is_root() or not ROOT_TWEAKS.get("priority_boost", True):
        return
    try:
        out = subprocess.check_output(["pidof", pkg], stderr=subprocess.STDOUT, text=True).strip()
        if not out: return
        pids = [p for p in out.split() if p.isdigit()]
    except Exception:
        return
    for pid in pids:
        run_quiet(["renice", "-n", "-5", "-p", pid])
        if has_bin("ionice"):
            run_quiet(["ionice", "-c2", "-n0", "-p", pid])
        if has_bin("taskset"):
            ncpu = os.cpu_count() or 1
            cpu_list = f"0-{max(0, ncpu-1)}"
            run_quiet(["taskset", "-pc", cpu_list, pid])

# ====================== HÀM TÁC VỤ (4) ==========================

def clear_cache_for_packages(packages):
    """
    SAFE: không xóa dữ liệu có thể chứa phiên đăng nhập.
    Chỉ xóa: cache/ và code_cache/
    KHÔNG xóa: app_webview/, shared_prefs/, databases/, files/ ...
    """
    results = []
    if not is_root():
        results.append("Không có quyền root: bỏ qua xóa cache.")
        return results
    for pkg in packages:
        base = f"/data/data/{pkg}"
        items = [
            ("cache", os.path.join(base, "cache")),
            ("code_cache", os.path.join(base, "code_cache")),
        ]
        for label, path in items:
            try:
                if not path.startswith("/data/data/"):
                    results.append(f"Bỏ qua {pkg}: đường dẫn {label} không hợp lệ."); continue
                if not os.path.isdir(path):
                    results.append(f"Không tìm thấy {label}: {pkg}"); continue
                code = os.system(f'rm -rf "{path}"/*')
                if code == 0: results.append(f"Đã xóa {label}: {pkg}")
                else: results.append(f"Lỗi xóa {label}: {pkg} (mã {code})")
            except Exception as e:
                results.append(f"Lỗi xóa {label}: {pkg} ({e})")
    return results

# ====================== FOCUS MODE (đóng app rác) ==========================

def list_user_installed_packages():
    PM = "/system/bin/pm" if os.path.exists("/system/bin/pm") else "pm"
    try:
        out = subprocess.check_output([PM, "list", "packages", "-3"], stderr=subprocess.STDOUT, text=True)
        return [line.split("package:",1)[1].strip() for line in out.splitlines() if line.startswith("package:")]
    except Exception:
        try:
            out = subprocess.check_output([PM, "list", "packages"], stderr=subprocess.STDOUT, text=True)
            pkgs = [line.split("package:", 1)[1].strip() for line in out.splitlines() if line.startswith("package:")]
            return [p for p in pkgs if not p.startswith(("com.android.", "android", "com.google.android."))]
        except Exception:
            return []

def focus_close_all_except(AM, whitelist, verbose=False):
    """Đóng (force-stop) tất cả app người dùng trừ whitelist. (verbose=False để không spam)"""
    closed = 0
    user_pkgs = list_user_installed_packages()
    if not user_pkgs:
        return 0
    wl = set(whitelist or [])
    for pkg in user_pkgs:
        if pkg in wl: continue
        try:
            subprocess.run([AM, "force-stop", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
            closed += 1
        except Exception:
            pass
    return closed

# ====================== KILL & REJOIN (theo lịch) ==========================

def scheduled_kill_and_rejoin(packages, AM, uri, pulse_delay):
    logs = []
    for pkg in packages:
        try:
            subprocess.run([AM, "force-stop", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
            time.sleep(0.5)
            cmd = [AM, "start", "-a", "android.intent.action.VIEW", "-d", uri, "-p", pkg]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
            boost_pkg_priority(pkg)
            time.sleep(max(pulse_delay, 0.5))
            logs.append(f"{pkg}: force-stop → start")
        except Exception as e:
            logs.append(f"{pkg}: lỗi {e}")
    return logs

# ====================== DASHBOARD (UI đóng khung) =================

def _clrscr():
    print("\033[2J\033[H", end='')

def draw_dashboard(title, place_id, pkgs, met, rows, start_ts):
    """
    Dashboard đóng khung theo layout:
      - Tiêu đề: Tool Rejoin BY ZNQ (căn giữa)
      - Dòng 'Ngày | tháng | năm: dd/mm/YYYY' bên trái và 'Uptime : …' bên phải
      - Bảng 4 cột: Package | Status | Info | Time
    """
    _clrscr()

    # Kích thước khung
    w_term = term_width(100)
    inner = max(70, min(140, w_term - 2))  # bề rộng bên trong khung
    bar = "═" * inner

    # Tiêu đề
    print(f"╔{bar}╗")
    title_str = " Tool Rejoin BY ZNQ ".center(inner, " ")
    print(f"║{title_str}║")

    # Dòng ngày/uptime
    date_str = time.strftime("%d/%m/%Y")
    uptime_str = _hms(int(time.time() - start_ts))
    left = f"Ngày | tháng | năm: {date_str}"
    right = f"Uptime : {uptime_str}"
    pad = max(1, inner - len(left) - len(right))
    print(f"║{left}{' ' * pad}{right}║")

    # Thanh phân cách dày
    print(f"╠{bar}╣")

    # Tính độ rộng các cột
    c_time = 10
    c_status = 12
    c_pkg = max(18, min(32, inner // 4))
    # có 3 dấu ' | ' = 9 ký tự
    c_info = max(20, inner - (c_pkg + c_status + c_time + 9))

    # Header bảng
    header = (
        f"{'Package'.ljust(c_pkg)} | "
        f"{'Status'.ljust(c_status)} | "
        f"{'Info'.ljust(c_info)} | "
        f"{'Time'.ljust(c_time)}"
    )
    print(f"║{header.ljust(inner)}║")

    # Đường kẻ mảnh giữa header và dữ liệu
    sep = f"{'─'*c_pkg}┼{'─'*c_status}┼{'─'*c_info}┼{'─'*c_time}"
    print(f"╟{sep.ljust(inner,'─')}╢")

    # In các hàng
    def clip(s, n):
        s = str(s or "")
        return s if len(s) <= n else (s[:max(0, n-1)] + "…")

    show_rows = rows if rows else [{"pkg":"", "status":"", "info":"", "time":""} for _ in range(4)]
    for r in show_rows:
        line = (
            f"{clip(r.get('pkg',''), c_pkg).ljust(c_pkg)} | "
            f"{clip(r.get('status',''), c_status).ljust(c_status)} | "
            f"{clip(r.get('info',''), c_info).ljust(c_info)} | "
            f"{clip(r.get('time',''), c_time).ljust(c_time)}"
        )
        print(f"║{line.ljust(inner)}║")

    # Footer
    print(f"╟{('Nhấn Ctrl+C để dừng.  |  Bản quyền: ZNQ').ljust(inner,' ')}╢")
    print(f"╚{bar}╝")

# ====================== CHỨC NĂNG CHÍNH =====================

def launch_and_maintain_roblox():
    if not check_psutil(): return
    cfg = load_config()
    if not cfg:
        print("❌ Chưa có cấu hình. Vào '2. Setup Tool' để lưu trước.\n")
        return

    # --- MIGRATE cấu hình cũ → mới ---
    changed = False
    raw_pk = cfg.get('packages', [])
    norm_pk = _normalize_packages(raw_pk)
    if norm_pk != raw_pk:
        cfg['packages'] = norm_pk; changed = True
    if 'place_id' in cfg:
        pid_raw = str(cfg.get('place_id', '')).strip()
        pid_norm = _digits_only(pid_raw)
        if pid_norm != pid_raw:
            cfg['place_id'] = pid_norm; changed = True
    if 'interval' not in cfg: cfg['interval'] = 60; changed = True
    if 'pulse_delay' not in cfg: cfg['pulse_delay'] = 2; changed = True
    if 'rejoin_every' not in cfg: cfg['rejoin_every'] = 5; changed = True
    if 'auto_clear_cache' not in cfg:
        cfg['auto_clear_cache'] = {'enabled': False, 'minutes': 0, 'packages': []}; changed = True
    if 'webhook_heartbeat_minutes' not in cfg:
        cfg['webhook_heartbeat_minutes'] = 0; changed = True
    if 'discord_webhook' not in cfg:
        cfg['discord_webhook'] = ""; changed = True
    if changed: save_config(cfg)
    # ---------------------------------

    if not cfg.get('packages') or not cfg.get('place_id'):
        print("❌ Cấu hình thiếu `packages` hoặc `place_id`. Vào '2. Setup Tool' để thiết lập lại.\n")
        return

    packages = list(dict.fromkeys([p.strip() for p in cfg.get('packages', []) if p]))
    place_id = str(cfg.get('place_id')).strip()

    try: interval = int(cfg.get('interval', 60))
    except Exception: interval = 60
    try: pulse_delay = int(cfg.get('pulse_delay', 2))
    except Exception: pulse_delay = 2
    interval = 60 if interval <= 0 else interval
    pulse_delay = 0 if pulse_delay < 0 else pulse_delay

    try: rejoin_every = int(cfg.get('rejoin_every', 5) or 5)
    except Exception: rejoin_every = 5
    if rejoin_every < 1: rejoin_every = 1
    cycle = 0

    # ---------- AutoClear nâng cao ----------
    acc = cfg.get('auto_clear_cache', {}) or {}
    acc_enabled = bool(acc.get('enabled', False))
    acc_minutes = int(acc.get('minutes', 0) or 0)
    acc_pkgs = acc.get('packages') or packages
    acc_next_ts = time.time() + (acc_minutes * 60) if (acc_enabled and acc_minutes > 0) else None
    acc_staggered = bool(acc.get('staggered', True))
    acc_only_if_ram = float(acc.get('only_if_ram_pct_over', 85))
    acc_skip_if_cpu = float(acc.get('skip_if_cpu_over_pct', 70))
    acc_jitter_sec  = int(acc.get('jitter_sec', 45))
    acc_cool_after_kill = int(acc.get('cooldown_after_kill_sec', 30))
    acc_include_termux = bool(acc.get('include_termux', False))
    acc_next_idx = 0
    kill_last_ts = None
    # ---------------------------------------

    webhook = (cfg.get('discord_webhook') or "").strip()
    try: hb_minutes = int(cfg.get('webhook_heartbeat_minutes', 0) or 0)
    except Exception: hb_minutes = 0
    hb_next_ts = time.time() + hb_minutes * 60 if hb_minutes > 0 else None

    # Hẹn giờ Kill & Rejoin theo phút (hỏi mỗi lần chạy)
    kill_enabled = False; kill_minutes = 0; kill_next_ts = None
    resp = input("\nBật hẹn giờ kill tap & rejoin? (y/n): ").strip().lower()
    if resp == 'y':
        try:
            km = int(input("Nhập chu kỳ (phút): ").strip() or "0")
            if km > 0:
                kill_minutes = km; kill_enabled = True
                kill_next_ts = time.time() + kill_minutes * 60
            else:
                print("⏱️ Số phút không hợp lệ → bỏ qua.")
        except Exception:
            print("⏱️ Không đọc được số phút → bỏ qua.")

    # >>> XÓA MÀN HÌNH + VẼ DASHBOARD NGAY
    start_ts = time.time()
    last_info = {pkg: {"status": "Init", "info": "Đang khởi tạo…", "time": time.strftime("%H:%M:%S")} for pkg in packages}
    if UI_CLEAR_AFTER_TIMER:
        met0 = collect_system_status(packages)
        rows0 = [{"pkg": p, "status": "Init", "info": "Chuẩn bị…", "time": time.strftime("%H:%M:%S")} for p in packages]
        draw_dashboard("ZNQ Rejoin Monitor", place_id, packages, met0, rows0, start_ts)

    AM = "/system/bin/am" if os.path.exists("/system/bin/am") else "am"
    uri = f"roblox://placeId={place_id}"

    if webhook:
        met = collect_system_status(packages)
        send_discord_embed(webhook, make_start_embed(place_id, packages, met))

    try:
        if ROOT_TWEAKS.get("doze_killer", True) or ROOT_TWEAKS.get("appops_whitelist", True):
            doze_killer_setup(packages)
            if webhook:
                met = collect_system_status(packages)
                send_discord_embed(webhook, make_root_embed(place_id, packages, met,
                    "Đã áp dụng Doze Killer, deviceidle whitelist, stay-awake & appops allow."))
        if FOCUS_MODE_ON_START:
            wl = set(packages) | set(TERMUX_WHITELIST)
            closed_count = focus_close_all_except(AM, wl, verbose=False)
            if packages:
                last_info[packages[0]] = {"status":"•", "info":f"FocusMode: đóng {closed_count} app", "time": time.strftime("%H:%M:%S")}
                draw_dashboard("ZNQ Rejoin Monitor", place_id, packages, collect_system_status(packages),
                               [{"pkg": p, "status": last_info[p]["status"], "info": last_info[p]["info"], "time": last_info[p]["time"]} for p in packages], start_ts)

        # Force-stop trước khi join đầu (im lặng)
        for pkg in packages:
            try: subprocess.run([AM, "force-stop", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
            except Exception: os.system(f'am force-stop {pkg}')
            time.sleep(0.15)

        # Join đầu (cập nhật bảng ngay)
        for pkg in packages:
            cmd = [AM, "start", "-a", "android.intent.action.VIEW", "-d", uri, "-p", pkg]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
            boost_pkg_priority(pkg)
            last_info[pkg] = {"status":"Joining", "info":"Khởi chạy lần đầu", "time": time.strftime("%H:%M:%S")}
            draw_dashboard("ZNQ Rejoin Monitor", place_id, packages, collect_system_status(packages),
                           [{"pkg": p, "status": last_info[p]["status"], "info": last_info[p]["info"], "time": last_info[p]["time"]} for p in packages], start_ts)
            time.sleep(pulse_delay)

        # Vòng giám sát
        while True:
            cycle += 1
            now = time.time()
            met = collect_system_status(packages)

            # ƯU TIÊN: Kill theo lịch
            if kill_enabled and kill_next_ts and now >= kill_next_ts:
                logs = scheduled_kill_and_rejoin(packages, AM, uri, pulse_delay)
                ts = time.strftime("%H:%M:%S")
                for pkg in packages:
                    last_info[pkg] = {"status": "Restart", "info": "Kill & Rejoin theo lịch", "time": ts}
                if webhook:
                    send_discord_embed(webhook, make_kill_embed(place_id, packages, met, kill_minutes, logs))
                kill_next_ts = now + kill_minutes * 60
                kill_last_ts = now
            else:
                # Join cơ chế lai
                for i, pkg in enumerate(packages, 1):
                    dead = not pkg_running(pkg)
                    periodic = (rejoin_every <= 1) or (cycle % rejoin_every == 1)
                    need_join = dead or periodic

                    if need_join:
                        cmd = [AM, "start", "-a", "android.intent.action.VIEW", "-d", uri, "-p", pkg]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)
                        boost_pkg_priority(pkg)
                        last_info[pkg] = {
                            "status": "Rejoin",
                            "info": "Do văng" if dead else f"Đến chu kỳ N={rejoin_every}",
                            "time": time.strftime("%H:%M:%S")
                        }
                        time.sleep(pulse_delay)
                    else:
                        last_info[pkg] = {
                            "status": "Online" if pkg_running(pkg) else "Offline",
                            "info": "Đang chạy, bỏ qua vòng này" if pkg_running(pkg) else "Không phát hiện tiến trình",
                            "time": time.strftime("%H:%M:%S")
                        }
                        time.sleep(0.03)

            # Heartbeat
            if webhook and hb_next_ts and now >= hb_next_ts:
                met_hb = collect_system_status(packages)
                send_discord_embed(webhook, make_heartbeat_embed(place_id, packages, met_hb))
                hb_next_ts = now + hb_minutes * 60

            # AutoClear an toàn (chỉ cache & code_cache)
            if acc_enabled and acc_minutes > 0 and acc_next_ts and now >= acc_next_ts:
                import random
                next_delay = acc_minutes * 60 + (random.randint(-acc_jitter_sec, acc_jitter_sec) if acc_jitter_sec>0 else 0)

                if kill_last_ts and (now - kill_last_ts) < acc_cool_after_kill:
                    acc_next_ts = now + max(10, next_delay)
                else:
                    met_now = collect_system_status(packages)
                    ram_pct = _as_float_pct(met_now.get('ram_pct'), 0)
                    cpu_pct = _as_float_pct(met_now.get('cpu'), 0)
                    can_clear = ram_pct >= acc_only_if_ram and cpu_pct <= acc_skip_if_cpu

                    pkgs_to_clear = list(acc_pkgs)
                    if not acc_include_termux:
                        pkgs_to_clear = [p for p in pkgs_to_clear if p != "com.termux"]
                    if acc_staggered and pkgs_to_clear:
                        acc_next_idx %= len(pkgs_to_clear)
                        pkgs_to_clear = [pkgs_to_clear[acc_next_idx]]
                        acc_next_idx += 1

                    if can_clear and pkgs_to_clear:
                        out = clear_cache_for_packages(pkgs_to_clear)
                        if webhook:
                            send_discord_embed(webhook, make_autoclear_embed(place_id, packages, met_now, out))
                        if pkgs_to_clear:
                            last_info[pkgs_to_clear[0]] = {"status":"Clean", "info":"Đã xóa cache (an toàn)", "time": time.strftime("%H:%M:%S")}
                    acc_next_ts = now + max(10, next_delay)

            # VẼ DASHBOARD
            rows = []
            for pkg in packages:
                st = "Online" if pkg_running(pkg) else "Offline"
                info = last_info.get(pkg, {}).get("info", "")
                shown = last_info.get(pkg, {}).get("status", st)
                tm = last_info.get(pkg, {}).get("time", time.strftime("%H:%M:%S"))
                rows.append({"pkg": pkg, "status": shown, "info": info, "time": tm})
            draw_dashboard("ZNQ Rejoin Monitor", place_id, packages, met, rows, start_ts)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nĐã dừng theo yêu cầu.")
        kill = input("Đóng tất cả tiến trình Roblox? (y/n): ").lower()
        if kill == 'y':
            for pkg in packages:
                try: os.system(f'am force-stop {pkg}')
                except Exception: pass
            print("Đã đóng xong.")
        doze_killer_teardown(packages)
        if webhook:
            met = collect_system_status(packages)
            send_discord_embed(webhook, make_stop_embed(place_id, packages, met))

# ====================== SETUP TOOL (CHỨC NĂNG 2) ==========================

def roblox_game_joiner():
    print_big_znq()
    print(center_line("--- Setup Tool (Lưu & Tham gia Game) ---"))

    cfg = load_config()
    if cfg:
        print("\nCấu hình hiện tại:")
        print(f"  Place ID         : {cfg.get('place_id')}")
        print(f"  Packages         : {', '.join(_normalize_packages(cfg.get('packages', [])))}")
        print(f"  interval (s)     : {cfg.get('interval', 60)}")
        print(f"  pulse_delay (s)  : {cfg.get('pulse_delay', 2)}")
        acc = cfg.get('auto_clear_cache', {}) or {}
        print(f"  AutoClear        : {'ON' if acc.get('enabled') else 'OFF'} ({acc.get('minutes',0)} phút)")
        hb = cfg.get('webhook_heartbeat_minutes', 0)
        print(f"  Webhook          : {(cfg.get('discord_webhook') or 'None')} | Heartbeat: {hb} phút")
        if input("\nDùng cấu hình cũ? (y/n): ").strip().lower() == 'y':
            launch_and_maintain_roblox(); return

    place_id = input("\nNhập Place ID: ").strip()
    if not place_id.isdigit():
        print("❌ Place ID không hợp lệ."); return

    print("\n--- Danh sách chọn nhanh ---")
    for k, v in APPLICATIONS.items(): print(f"  {k}: {v}")
    print("  2. Nhập thủ công (tự dán nhiều package)")
    sel = input("Chọn (ví dụ: 1 hoặc 2): ").strip()

    selected = []
    tokens = sel.replace(',', ' ').split() if sel else []
    manual = False
    for t in tokens:
        if t == '2':
            manual = True
        else:
            try:
                idx = int(t); key = f"{idx}. "
                for name, pkg in APPLICATIONS.items():
                    if name.startswith(key):
                        selected.append(pkg); break
            except: pass
    if manual or not tokens:
        selected = get_packages_from_user_input()

    selected = list(dict.fromkeys([p.strip() for p in selected if p]))
    if not selected:
        print("❌ Chưa chọn package nào."); return

    try: interval = int(input("Chu kỳ gửi lại lệnh (giây, Enter=60): ").strip() or "60")
    except: interval = 60
    try: pulse_delay = int(input("Độ trễ giữa từng app (giây, Enter=2): ").strip() or "2")
    except: pulse_delay = 2
    if interval <= 0: interval = 60
    if pulse_delay < 0: pulse_delay = 0

    new_cfg = {
        'place_id': place_id,
        'packages': selected,
        'interval': interval,
        'pulse_delay': pulse_delay,
        'rejoin_every': 5
    }
    if save_config(new_cfg):
        print("\n✅ Đã lưu cấu hình!")
        if input("Join ngay bây giờ? (y/n): ").strip().lower() == 'y':
            launch_and_maintain_roblox()

# ====================== SETUP PACK ==========================

def setup_pack():
    print_big_znq()
    print(center_line("--- Setup Pack (autoexec) ---"))
    if not is_root():
        print("❌ Yêu cầu root để truy cập /data/data"); input("\nEnter để về…"); return

    print("\n--- Danh sách chọn nhanh ---")
    for k, v in APPLICATIONS.items(): print(f"  {k}: {v}")
    print("  2. Nhập thủ công (tự dán nhiều package)")
    sel = input("Chọn (1 hoặc 2): ").strip()

    selected = []
    tokens = sel.replace(',', ' ').split() if sel else []
    manual = False
    for t in tokens:
        if t == '2': manual = True
        else:
            try:
                idx = int(t); key = f"{idx}. "
                for name, pkg in APPLICATIONS.items():
                    if name.startswith(key): selected.append(pkg); break
            except: pass
    if manual or not tokens:
        selected = get_packages_from_user_input()

    selected = list(dict.fromkeys([p.strip() for p in selected if p]))
    if not selected:
        print("❌ Chưa chọn package."); input("\nEnter…"); return

    for pkg in selected:
        autoexec = f"/data/data/{pkg}/files/autoexec"
        try:
            os.makedirs(autoexec, exist_ok=True)
            print(f"✅ {autoexec}")
        except Exception as e:
            print(f"❌ {pkg}: {e}")
    input("\nXong. Enter để quay lại…")

# ====================== INSTALL REQS ========================

def install_requirements():
    print_big_znq()
    print(center_line("--- Cài đặt gói cần thiết ---"))
    print("Gợi ý: pkg update && pkg install tsu -y | pip install psutil certifi\n")
    cmd = input("Nhập lệnh cần chạy (trống = bỏ qua): ").strip()
    if not cmd:
        print("Bỏ qua."); time.sleep(1); return
    print(f"\n▶️  Thực thi: {cmd}\n")
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = p.stdout.readline()
            if line == b'' and p.poll() is not None: break
            if line: print(line.decode('utf-8', 'ignore').rstrip())
        print("\n✅ Thành công!" if p.returncode == 0 else "\n❌ Có lỗi khi cài đặt.")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
    input("\nEnter để quay lại…")

# ====================== SETTINGS ===========================

def settings_menu():
    while True:
        print_big_znq()
        print(center_line("--- SETTINGS ---"))
        cfg = load_config() or {}
        acc = cfg.get('auto_clear_cache', {}) or {}
        hb = cfg.get('webhook_heartbeat_minutes', 0)
        print("\nTrạng thái hiện tại:")
        print(f" - AutoClear: {'ON' if acc.get('enabled') else 'OFF'} ({acc.get('minutes',0)} phút; "
              f"pk={', '.join(acc.get('packages', []) or cfg.get('packages', []) or [])})")
        print(f" - Webhook  : {cfg.get('discord_webhook') or 'None'} | Heartbeat: {hb} phút")
        ch = input("\n1) Auto xóa cache   2) Discord Webhook   0) Quay lại  → ").strip()
        if ch == '1': setup_autoclear()
        elif ch == '2': setup_webhook()
        elif ch == '0': return
        else: print("Lựa chọn không hợp lệ."); time.sleep(1)

def setup_autoclear():
    print_big_znq(); print(center_line("--- Auto xóa cache ---"))
    cfg = load_config() or {}; cur = cfg.get('auto_clear_cache', {}) or {}
    print(f"\nHiện tại: {'ON' if cur.get('enabled') else 'OFF'} / {cur.get('minutes',0)} phút\n(Chỉ xóa cache & code_cache — KHÔNG đăng xuất)")

    enabled = (input("Bật? (y/n): ").strip().lower() == 'y')
    minutes = 0; selected = []
    if enabled:
        try: minutes = int(input("Chu kỳ xóa (phút): ").strip() or "30")
        except: minutes = 30
        if minutes <= 0: minutes = 30

        print("\n--- Danh sách chọn nhanh ---")
        for k,v in APPLICATIONS.items(): print(f"  {k}: {v}")
        print("  2. Nhập thủ công (tự dán nhiều package)")
        sel = input("Chọn (1 hoặc 2; Enter = giữ danh sách cũ/đang chạy): ").strip()
        if sel:
            tokens = sel.replace(',', ' ').split()
            manual = False
            for t in tokens:
                if t == '2': manual = True
                else:
                    try:
                        idx = int(t); key = f"{idx}. "
                        for name,pkg in APPLICATIONS.items():
                            if name.startswith(key): selected.append(pkg); break
                    except: pass
            if manual:
                selected = get_packages_from_user_input()
        if not selected: selected = cur.get('packages') or (cfg.get('packages') or [])

        selected = list(dict.fromkeys([p.strip() for p in selected if p]))
        if not selected:
            print("❌ Không có package nào."); input("\nEnter…"); return

        cfg['auto_clear_cache'] = {'enabled': True, 'minutes': minutes, 'packages': selected}
        print(f"\n✅ Đã bật AutoClear mỗi {minutes} phút cho: {', '.join(selected)}")
        ensure_root_note()
    else:
        cfg['auto_clear_cache'] = {'enabled': False, 'minutes': 0, 'packages': []}
        print("\n✅ Đã tắt AutoClear.")

    save_config(cfg); input("\nEnter để quay lại…")

def setup_webhook():
    print_big_znq(); print(center_line("--- Discord Webhook ---"))
    cfg = load_config() or {}
    cur = cfg.get('discord_webhook') or ''; hb = cfg.get('webhook_heartbeat_minutes', 0)
    print(f"\nWebhook hiện tại : {cur or 'None'}")
    print(f"Heartbeat hiện tại: {hb} phút (0 = tắt)")
    url = input("Nhập URL webhook (để trống để xóa): ").strip()
    if not url:
        cfg['discord_webhook'] = ""; print("Đã xóa webhook.")
    else:
        cfg['discord_webhook'] = url
        try: hb_val = int(input("Đặt heartbeat (phút, 0=tắt, Enter=15): ").strip() or "15")
        except: hb_val = 15
        if hb_val < 0: hb_val = 0
        cfg['webhook_heartbeat_minutes'] = hb_val
        print(f"Đã cập nhật webhook, heartbeat={hb_val} phút.")
        if input("Gửi tin nhắn thử? (y/n): ").strip().lower() == 'y':
            ok, msg = post_discord(url, f"✅ Webhook test ok | {human_time()}")
            print("Kết quả:", "Thành công" if ok else f"Thất bại ({msg})")
    save_config(cfg); input("\nEnter để quay lại…")

# ====================== MENU CHÍNH ==========================

def main_menu():
    while True:
        print_big_znq()
        print()
        print(center_line("1. Khởi chạy & Giám sát"))
        print(center_line("2. Setup Tool (Lưu & Tham gia Game)"))
        print(center_line("3. Setup Pack (Tạo thư mục autoexec)"))
        print(center_line("4. Cài đặt các gói cần thiết"))
        print(center_line("5. Cài đặt (Settings)"))
        print(center_line("0. Thoát"))
        ch = input("\nChọn công cụ: ").strip()
        if ch == '1': launch_and_maintain_roblox()
        elif ch == '2': roblox_game_joiner()
        elif ch == '3': setup_pack()
        elif ch == '4': install_requirements()
        elif ch == '5': settings_menu()
        elif ch == '0': break
        else: print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main_menu()
