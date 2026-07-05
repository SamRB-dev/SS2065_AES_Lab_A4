from flask import Flask, jsonify, render_template_string
import sqlite3
import time

app = Flask(__name__)

# Adjust this to wherever your actual database file lives relative to
# wherever you run "python app.py" from.
DB_PATH = "../../db/Sensor_Reading_Records.db"

# Status thresholds, in seconds, since a sensor's last received reading.
LIVE_THRESHOLD = 10      # under this: shown as LIVE
DELAYED_THRESHOLD = 30    # under this: shown as DELAYED, otherwise OFFLINE


def get_connection():
    # WAL mode lets this Flask app read the database at the same time
    # your MQTT subscriber is writing to it, without "database is locked" errors.
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def compute_status(last_timestamp):
    """Given a Unix epoch timestamp, return (status_string, seconds_ago)."""
    if last_timestamp is None:
        return "offline", None

    seconds_ago = int(time.time()) - int(last_timestamp)

    if seconds_ago <= LIVE_THRESHOLD:
        return "ok", seconds_ago
    elif seconds_ago <= DELAYED_THRESHOLD:
        return "warn", seconds_ago
    else:
        return "danger", seconds_ago


def latest_temperature_humidity(cursor):
    cursor.execute("""
        SELECT timestamp, temperature, humidity
        FROM temperature_humidity_readings
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        return None, None, None
    return row  # (timestamp, temperature, humidity)


def latest_light(cursor):
    cursor.execute("""
        SELECT timestamp, light_intensity
        FROM photoresistor_readings
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        return None, None
    return row  # (timestamp, light_intensity)


def latest_noise(cursor):
    cursor.execute("""
        SELECT timestamp, sound_level
        FROM microphone_readings
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        return None, None
    return row  # (timestamp, sound_level)


def historical_range(cursor, table, column):
    """Returns (min_value, max_value) across all rows ever stored."""
    cursor.execute(f"SELECT MIN({column}), MAX({column}) FROM {table}")
    row = cursor.fetchone()
    return row if row else (None, None)


def to_percentage(value, minimum, maximum):
    """Scales a raw value to 0-100 based on the historical min/max seen so far."""
    if value is None or minimum is None or maximum is None or maximum == minimum:
        return None
    pct = (value - minimum) / (maximum - minimum) * 100
    return round(max(0, min(100, pct)), 1)


@app.route("/api/current")
def api_current():
    conn = get_connection()
    cursor = conn.cursor()

    th_ts, temperature, humidity = latest_temperature_humidity(cursor)
    light_ts, light_raw = latest_light(cursor)
    noise_ts, noise_raw = latest_noise(cursor)

    light_min, light_max = historical_range(cursor, "photoresistor_readings", "light_intensity")
    noise_min, noise_max = historical_range(cursor, "microphone_readings", "sound_level")

    conn.close()

    th_status, th_seconds = compute_status(th_ts)
    light_status, light_seconds = compute_status(light_ts)
    noise_status, noise_seconds = compute_status(noise_ts)

    return jsonify({
        "temperature_humidity": {
            "temperature": temperature,
            "humidity": humidity,
            "status": th_status,
            "seconds_ago": th_seconds,
            "timestamp": th_ts
        },
        "light": {
            "voltage": light_raw,
            "percentage": to_percentage(light_raw, light_min, light_max),
            "range_min": light_min,
            "range_max": light_max,
            "status": light_status,
            "seconds_ago": light_seconds,
            "timestamp": light_ts
        },
        "noise": {
            "voltage": noise_raw,
            "percentage": to_percentage(noise_raw, noise_min, noise_max),
            "range_min": noise_min,
            "range_max": noise_max,
            "status": noise_status,
            "seconds_ago": noise_seconds,
            "timestamp": noise_ts
        }
    })


@app.route("/api/stats")
def api_stats():
    conn = get_connection()
    cursor = conn.cursor()

    def all_time(table, column):
        cursor.execute(f"SELECT MAX({column}), MIN({column}), AVG({column}) FROM {table}")
        peak, low, avg = cursor.fetchone()
        avg = round(avg, 1) if avg is not None else None
        return {"peak": peak, "low": low, "avg": avg}

    def today(table, column):
        # 'unixepoch' modifier is required because our timestamps are stored
        # as Unix epoch integers, not SQLite's native datetime strings.
        cursor.execute(f"""
            SELECT MAX({column}), MIN({column}), AVG({column})
            FROM {table}
            WHERE date(timestamp, 'unixepoch') = date('now')
        """)
        high, low, avg = cursor.fetchone()
        avg = round(avg, 1) if avg is not None else None
        return {"high": high, "low": low, "avg": avg}

    stats = {
        "temperature": {
            "today":    today("temperature_humidity_readings", "temperature"),
            "all_time": all_time("temperature_humidity_readings", "temperature"),
        },
        "humidity": {
            "today":    today("temperature_humidity_readings", "humidity"),
            "all_time": all_time("temperature_humidity_readings", "humidity"),
        },
        "light": {
            "today":    today("photoresistor_readings", "light_intensity"),
            "all_time": all_time("photoresistor_readings", "light_intensity"),
        },
        "noise": {
            "today":    today("microphone_readings", "sound_level"),
            "all_time": all_time("microphone_readings", "sound_level"),
        },
    }

    conn.close()
    return jsonify(stats)


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Smart Room Monitor</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet" />
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #10111A; --panel: #171926; --border: #262A3A;
    --indigo: #7C8CFF; --teal: #2DD4C8; --amber: #FBBF24; --red: #F87171;
    --text: #EEEFF7; --muted: #888DA3;
    --sans: 'Inter', sans-serif; --mono: 'JetBrains Mono', monospace;
  }
  body { background: var(--bg); color: var(--text); font-family: var(--sans); padding: 2rem 2.5rem; max-width: 1280px; margin: 0 auto; }
  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
  h1 { font-size: 1.2rem; font-weight: 700; }
  .sub { font-size: 0.75rem; color: var(--muted); }
  .status-chip { font-size: 0.75rem; display: flex; align-items: center; gap: 0.4rem; }
  .status-chip .dot { width: 6px; height: 6px; border-radius: 50%; }
  .status-chip.ok { color: var(--teal); } .status-chip.ok .dot { background: var(--teal); }
  .status-chip.warn { color: var(--amber); } .status-chip.warn .dot { background: var(--amber); }
  .status-chip.down { color: var(--red); } .status-chip.down .dot { background: var(--red); }

  .spotlight-grid { display: grid; grid-template-columns: 1.3fr 1fr; gap: 1.25rem; margin-bottom: 1.25rem; }
  .spotlight-card { background: linear-gradient(160deg, #1B1E2D, #171926); border: 1px solid var(--border); border-radius: 18px; padding: 2.25rem; display: flex; align-items: center; gap: 2rem; }
  .ring-wrap-xl { position: relative; width: 180px; height: 180px; flex-shrink: 0; }
  .ring-wrap-xl svg { transform: rotate(-90deg); }
  .ring-bg { fill: none; stroke: var(--border); stroke-width: 12; }
  .ring-fg { fill: none; stroke: var(--indigo); stroke-width: 12; stroke-linecap: round; transition: stroke-dashoffset 0.6s; }
  .ring-value-xl { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-family: var(--mono); font-size: 2.7rem; font-weight: 700; }
  .ring-unit-xl { position: absolute; top: 67%; left: 50%; transform: translate(-50%, -50%); font-size: 0.85rem; color: var(--muted); }

  .spotlight-detail .label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 0.6rem; }
  .spotlight-detail .metric { font-size: 1.1rem; margin-bottom: 0.5rem; font-family: var(--mono); }
  .spotlight-detail .status { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; margin-top: 1rem; }
  .spotlight-detail .status .dot { width: 7px; height: 7px; border-radius: 50%; }

  .side-stack { display: flex; flex-direction: column; gap: 1.25rem; }
  .compact-card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 1.4rem; }
  .compact-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin-bottom: 0.75rem; }
  .compact-value { font-family: var(--mono); font-size: 1.9rem; font-weight: 700; margin-bottom: 0.2rem; }
  .compact-value .calc { font-family: var(--sans); font-size: 0.78rem; font-weight: 400; color: var(--muted); margin-left: 0.4rem; }

  .zone-endpoints { display: flex; justify-content: space-between; font-family: var(--mono); font-size: 0.62rem; color: var(--muted); margin: 0.6rem 0 0.35rem; }
  .zone-track { position: relative; display: flex; height: 6px; border-radius: 3px; overflow: visible; }
  .zone { flex: 1; }
  .zone:first-child { border-radius: 3px 0 0 3px; } .zone:last-child { border-radius: 0 3px 3px 0; }
  .zone.low { background: rgba(124,140,255,0.25); } .zone.mid { background: rgba(45,212,200,0.3); } .zone.high { background: rgba(251,191,36,0.3); }
  .zone-marker { position: absolute; top: -3px; width: 2px; height: 12px; background: var(--text); transform: translateX(-50%); transition: left 0.6s; }

  .compact-status { display: flex; align-items: center; gap: 0.4rem; font-size: 0.72rem; margin-top: 0.8rem; }
  .dot-status { width: 6px; height: 6px; border-radius: 50%; }
  .dot-status.ok { background: var(--teal); } .dot-status.warn { background: var(--amber); } .dot-status.down { background: var(--red); }
  .compact-status.ok-text { color: var(--teal); } .compact-status.warn-text { color: var(--amber); } .compact-status.down-text { color: var(--red); }

  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; }
  .panel h2 { font-size: 0.82rem; font-weight: 600; margin-bottom: 1rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
  .log-row { display: flex; justify-content: space-between; font-size: 0.78rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
  .log-row:last-child { border-bottom: none; }
  .log-row .time { font-family: var(--mono); color: var(--muted); font-size: 0.7rem; }

  .units-strip { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; margin-bottom: 1.25rem; }
  .units-strip h2 { font-size: 0.85rem; font-weight: 600; margin-bottom: 1.1rem; }
  .units-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
  .units-row h3 { font-size: 0.78rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem; }
  .units-row h3 .swatch { width: 8px; height: 8px; border-radius: 2px; }
  .units-row p { font-size: 0.75rem; color: var(--muted); line-height: 1.55; margin-bottom: 0.45rem; }
  .units-row .example { font-size: 0.72rem; color: var(--text); background: rgba(124,140,255,0.08); border-left: 2px solid var(--indigo); padding: 0.45rem 0.65rem; border-radius: 0 6px 6px 0; }

  .stats-section { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 1.75rem; margin-bottom: 1.25rem; }
  .stats-section > h2 { font-size: 1rem; font-weight: 600; margin-bottom: 1.5rem; }
  .stats-scope-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .stats-scope-label { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 1rem; }
  .stats-scope-label .scope-dot { width: 7px; height: 7px; border-radius: 50%; }
  .stats-scope-label.today .scope-dot { background: var(--teal); }
  .stats-scope-label.alltime .scope-dot { background: var(--indigo); }
  .stats-full-table { width: 100%; border-collapse: collapse; }
  .stats-full-table th { text-align: left; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); font-weight: 600; padding: 0.7rem 0.6rem; border-bottom: 1px solid var(--border); }
  .stats-full-table th:not(:first-child), .stats-full-table td:not(:first-child) { text-align: right; }
  .stats-full-table td { padding: 0.85rem 0.6rem; font-family: var(--mono); font-size: 0.95rem; border-bottom: 1px solid var(--border); }
  .stats-full-table tr:last-child td { border-bottom: none; }
  .stats-full-table td.name { font-family: var(--sans); font-weight: 600; font-size: 0.85rem; }
  .stats-full-table .u { font-size: 0.68rem; color: var(--muted); margin-left: 0.2rem; }
  .stats-full-table td.hi { color: var(--red); }
  .stats-full-table td.lo { color: var(--indigo); }
  .stats-note { margin-top: 1.25rem; font-size: 0.72rem; color: var(--muted); }
</style>
</head>
<body>

<header>
  <div>
    <h1>Smart Room Monitor</h1>
    <div class="sub">HSHL Advanced Embedded Systems Lab</div>
  </div>
  <div class="status-chip" id="pageStatus"><div class="dot"></div> <span id="pageStatusText">Checking data...</span></div>
</header>

<div class="spotlight-grid">

  <div class="spotlight-card">
    <div class="ring-wrap-xl">
      <svg viewBox="0 0 180 180">
        <circle class="ring-bg" cx="90" cy="90" r="76"/>
        <circle class="ring-fg" cx="90" cy="90" r="76" stroke-dasharray="478" stroke-dashoffset="478" id="ring-temp"/>
      </svg>
      <div class="ring-value-xl" id="val-temp">--</div>
      <div class="ring-unit-xl">&deg;C</div>
    </div>
    <div class="spotlight-detail">
      <div class="label">Temperature &amp; Humidity</div>
      <div class="metric" id="val-hum">Humidity --%</div>
      <div class="metric" style="color:var(--muted); font-size:0.85rem;">Sensor KY-015</div>
      <div class="status" id="status-th"><div class="dot"></div> <span id="status-th-text">Waiting for data</span></div>
    </div>
  </div>

  <div class="side-stack">
    <div class="compact-card">
      <div class="compact-label">Light Intensity</div>
      <div class="compact-value" id="val-light">-- V</div>
      <div class="zone-endpoints" id="zone-light-endpoints"><span>-- V</span><span>-- V</span></div>
      <div class="zone-track"><div class="zone low"></div><div class="zone mid"></div><div class="zone high"></div><div class="zone-marker" id="marker-light" style="left:0%;"></div></div>
      <div class="compact-status" id="status-light"><div class="dot-status"></div> <span id="status-light-text">Waiting for data</span></div>
    </div>
    <div class="compact-card">
      <div class="compact-label">Sound Level</div>
      <div class="compact-value" id="val-noise">-- V</div>
      <div class="zone-endpoints" id="zone-noise-endpoints"><span>-- V</span><span>-- V</span></div>
      <div class="zone-track"><div class="zone low"></div><div class="zone mid"></div><div class="zone high"></div><div class="zone-marker" id="marker-noise" style="left:0%;"></div></div>
      <div class="compact-status" id="status-noise"><div class="dot-status"></div> <span id="status-noise-text">Waiting for data</span></div>
    </div>
  </div>

</div>

<div class="panel" style="margin-bottom: 1.25rem;">
  <h2>Recent Activity</h2>
  <div id="eventList">
    <div class="log-row"><span>Waiting for the first reading to arrive&hellip;</span></div>
  </div>
</div>

<div class="stats-section">
  <h2>Sensor Statistics</h2>
  <div class="stats-scope-grid">

    <div class="stats-scope">
      <div class="stats-scope-label today"><div class="scope-dot"></div> Today</div>
      <table class="stats-full-table">
        <thead><tr><th>Reading</th><th>High</th><th>Low</th><th>Average</th></tr></thead>
        <tbody id="statsTodayBody">
          <tr><td colspan="4">Loading&hellip;</td></tr>
        </tbody>
      </table>
    </div>

    <div class="stats-scope">
      <div class="stats-scope-label alltime"><div class="scope-dot"></div> All-Time</div>
      <table class="stats-full-table">
        <thead><tr><th>Reading</th><th>Peak</th><th>Low</th><th>Average</th></tr></thead>
        <tbody id="statsAllTimeBody">
          <tr><td colspan="4">Loading&hellip;</td></tr>
        </tbody>
      </table>
    </div>

  </div>
  <div class="stats-note">For Light and Sound, the lowest voltage corresponds to the brightest or loudest reading, since both sensors work on an inverted scale. Refer to the sensor cards above for the plain-language reading.</div>
</div>

<div class="units-strip">
  <h2>Understanding the Units</h2>
  <div class="units-row">
    <div>
      <h3><span class="swatch" style="background:var(--indigo);"></span>Temperature &amp; Humidity</h3>
      <p>Direct calibrated readings from the KY-015. Higher numbers mean warmer or more humid conditions.</p>
    </div>
    <div>
      <h3><span class="swatch" style="background:var(--amber);"></span>Light Intensity</h3>
      <p>The KY-018 outputs a voltage that falls as light increases. Lower voltage means brighter, higher means darker.</p>
      <div class="example">e.g. low voltage &rarr; well-lit room. High voltage &rarr; near darkness.</div>
    </div>
    <div>
      <h3><span class="swatch" style="background:var(--red);"></span>Sound Level</h3>
      <p>The KY-037 outputs an inverted voltage. Lower voltage means louder, higher means quieter.</p>
      <div class="example">e.g. low voltage &rarr; a loud clap. High voltage &rarr; near silence.</div>
    </div>
  </div>
</div>

<script>
  const STATUS_LABEL = { ok: "LIVE", warn: "DELAYED", danger: "OFFLINE" };
  const STATUS_CSS   = { ok: "ok", warn: "warn", danger: "down" };

  function timeText(secondsAgo) {
    if (secondsAgo === null) return "no data yet";
    if (secondsAgo <= 2) return "updated moments ago";
    return `${secondsAgo} seconds ago`;
  }

  function applyStatus(prefix, status, secondsAgo) {
    const cls = STATUS_CSS[status] || "down";
    const wrap = document.getElementById(`status-${prefix}`);
    const text = document.getElementById(`status-${prefix}-text`);
    const dot = wrap.querySelector(".dot, .dot-status");

    wrap.className = wrap.className.split(" ")[0] + " " + cls + "-text";
    dot.className = dot.className.split(" ")[0] + " " + cls;
    text.textContent = `${STATUS_LABEL[status] || "OFFLINE"} \u00b7 ${timeText(secondsAgo)}`;
  }

  function logEvent(message) {
    const list = document.getElementById("eventList");
    const now = new Date().toLocaleTimeString("en-GB", { hour12: false });
    const row = document.createElement("div");
    row.className = "log-row";
    row.innerHTML = `<span>${message}</span><span class="time">${now}</span>`;
    list.prepend(row);
    while (list.children.length > 8) list.removeChild(list.lastChild);
  }

  let lastSeenTemp = null, lastSeenLight = null, lastSeenNoise = null;

  async function refreshCurrent() {
    try {
      const res = await fetch("/api/current");
      const data = await res.json();
      let onlineCount = 0;
      let anyLive = false;

      const th = data.temperature_humidity;
      if (th.temperature !== null) {
        document.getElementById("val-temp").textContent = th.temperature;
        document.getElementById("val-hum").textContent = `Humidity ${th.humidity}%`;
        const offset = 478 - Math.max(0, Math.min(1, (th.temperature - 0) / 50)) * 478;
        document.getElementById("ring-temp").style.strokeDashoffset = offset;
        if (th.timestamp !== lastSeenTemp) {
          logEvent(`Temperature/humidity reading received, ${th.temperature}\u00b0C`);
          lastSeenTemp = th.timestamp;
        }
      }
      applyStatus("th", th.status, th.seconds_ago);
      if (th.status !== "danger") { onlineCount++; anyLive = true; }

      const light = data.light;
      if (light.voltage !== null) {
        document.getElementById("val-light").textContent = `${light.voltage} V`;
        document.getElementById("zone-light-endpoints").innerHTML =
          `<span>${light.range_min} V</span><span>${light.range_max} V</span>`;
        document.getElementById("marker-light").style.left = `${light.percentage ?? 0}%`;
        if (light.timestamp !== lastSeenLight) {
          logEvent(`Light reading received, ${light.voltage} V`);
          lastSeenLight = light.timestamp;
        }
      }
      applyStatus("light", light.status, light.seconds_ago);
      if (light.status !== "danger") { onlineCount++; anyLive = true; }

      const noise = data.noise;
      if (noise.voltage !== null) {
        document.getElementById("val-noise").textContent = `${noise.voltage} V`;
        document.getElementById("zone-noise-endpoints").innerHTML =
          `<span>${noise.range_min} V</span><span>${noise.range_max} V</span>`;
        document.getElementById("marker-noise").style.left = `${noise.percentage ?? 0}%`;
        if (noise.timestamp !== lastSeenNoise) {
          logEvent(`Sound reading received, ${noise.voltage} V`);
          lastSeenNoise = noise.timestamp;
        }
      }
      applyStatus("noise", noise.status, noise.seconds_ago);
      if (noise.status !== "danger") { onlineCount++; anyLive = true; }

      const pageStatus = document.getElementById("pageStatus");
      const pageStatusText = document.getElementById("pageStatusText");
      pageStatus.className = "status-chip " + (anyLive ? "ok" : "down");
      pageStatusText.textContent = anyLive
        ? `${onlineCount} / 3 sensors reporting`
        : "No recent data from any sensor";

    } catch (err) {
      console.error("Failed to fetch /api/current", err);
    }
  }

  function renderStatsTable(bodyId, data, keys, labels) {
    const body = document.getElementById(bodyId);
    body.innerHTML = "";
    const rows = [
      ["Temperature", data.temperature, "\u00b0C"],
      ["Humidity",    data.humidity,    "%"],
      ["Light",       data.light,       "V"],
      ["Sound",       data.noise,       "V"],
    ];
    rows.forEach(([name, vals, unit]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="name">${name}</td>
        <td class="hi">${vals[keys[0]] ?? "--"}<span class="u">${unit}</span></td>
        <td class="lo">${vals[keys[1]] ?? "--"}<span class="u">${unit}</span></td>
        <td>${vals[keys[2]] ?? "--"}<span class="u">${unit}</span></td>`;
      body.appendChild(tr);
    });
  }

  async function refreshStats() {
    try {
      const res = await fetch("/api/stats");
      const s = await res.json();

      const today = {
        temperature: s.temperature.today, humidity: s.humidity.today,
        light: s.light.today, noise: s.noise.today
      };
      const allTime = {
        temperature: s.temperature.all_time, humidity: s.humidity.all_time,
        light: s.light.all_time, noise: s.noise.all_time
      };

      renderStatsTable("statsTodayBody", today, ["high", "low", "avg"]);
      renderStatsTable("statsAllTimeBody", allTime, ["peak", "low", "avg"]);
    } catch (err) {
      console.error("Failed to fetch /api/stats", err);
    }
  }

  refreshCurrent();
  refreshStats();
  setInterval(refreshCurrent, 4000);
  setInterval(refreshStats, 15000);
</script>

</body>
</html>
"""




@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


if __name__ == "__main__":
    # host="0.0.0.0" makes it reachable from other devices on the network,
    # not just from the Pi itself, useful during your presentation.
    app.run(host="0.0.0.0", port=5000, debug=True)