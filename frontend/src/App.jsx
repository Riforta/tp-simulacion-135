import { useMemo, useState } from "react";

const API = "http://127.0.0.1:8000";

function beautifyHeader(col) {
  const fixedMap = {
    fila: "Fila",
    evento: "Evento",
    reloj: "Reloj",
    cola: "Cola",
    cantPiezas: "Piezas",
    rndHorno: "RND Horno",
    tiempoHorno: "Tiempo Horno",
    finHorno: "Fin Horno",
    estadoHorno: "Estado Horno",
    cantEnsambladores: "Ensambladores",
    promedioPiezas: "Promedio piezas",
    minPiezas: "Mín piezas",
    maxPiezas: "Máx piezas",
    repeticiones: "Repeticiones",
  };

  if (fixedMap[col]) return fixedMap[col];

  let m = col.match(/^rndEnsamble(\d+)$/);
  if (m) return `RND Ens ${m[1]}`;

  m = col.match(/^tiempoEnsamble(\d+)$/);
  if (m) return `Tiempo Ens ${m[1]}`;

  m = col.match(/^finEnsamble(\d+)$/);
  if (m) return `Fin Ens ${m[1]}`;

  m = col.match(/^estadoComp(\d+)$/);
  if (m) return `Comp ${m[1]} Estado`;

  return col;
}

function DataTable({ columns, rows }) {
  if (!columns?.length || !rows?.length) return <p>No hay datos.</p>;

  return (
    <div style={{ overflowX: "auto", maxHeight: "65vh", overflowY: "auto", border: "1px solid #ddd", borderRadius: 8 }}>
      <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 14 }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c}
                title={c}
                style={{
                  textAlign: "left",
                  padding: "8px 10px",
                  borderBottom: "1px solid #ddd",
                  whiteSpace: "nowrap",
                  background: "#f7f7f7",
                  position: "sticky",
                  top: 0,
                }}
              >
                {beautifyHeader(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td
                  key={c}
                  style={{
                    padding: "6px 10px",
                    borderBottom: "1px solid #eee",
                    whiteSpace: "nowrap",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {String(r[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NumberInput({ label, value, onChange, min, step }) {
  return (
    <label style={{ display: "grid", gap: 4 }}>
      <span>{label}</span>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
        step={step}
      />
    </label>
  );
}

export default function App() {
  const [tab, setTab] = useState("resumen");

  // Parámetros del modelo (compartidos)
  const [ensambleMin, setEnsambleMin] = useState(25);
  const [ensambleMax, setEnsambleMax] = useState(35);
  const [hornoMin, setHornoMin] = useState(6);
  const [hornoMax, setHornoMax] = useState(10);
  const [prioridadEmpate, setPrioridadEmpate] = useState("ensamble"); // "ensamble" | "horno"

  // Resumen (sweep)
  const [maxEnsambladores, setMaxEnsambladores] = useState(10);
  const [repeticiones, setRepeticiones] = useState(200);
  const [minutosResumen, setMinutosResumen] = useState(480);
  const [seedBase, setSeedBase] = useState(123);
  const [summary, setSummary] = useState(null);

  // Detalle (single)
  const [cantEnsambladores, setCantEnsambladores] = useState(3);
  const [minutosDetalle, setMinutosDetalle] = useState(480);
  const [seedDetalle, setSeedDetalle] = useState(123);
  const [detail, setDetail] = useState(null);

  // Filtro filas (detalle)
  const [filaDesde, setFilaDesde] = useState("");
  const [filaHasta, setFilaHasta] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function bodyConfig() {
    return {
      ensamble_min: Number(ensambleMin),
      ensamble_max: Number(ensambleMax),
      horno_min: Number(hornoMin),
      horno_max: Number(hornoMax),
      prioridad_empate: prioridadEmpate,
    };
  }

  async function correrResumen() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/simulate_sweep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          max_ensambladores: Number(maxEnsambladores),
          minutos: Number(minutosResumen),
          repeticiones: Number(repeticiones),
          seed_base: seedBase === "" ? null : Number(seedBase),
          ...bodyConfig(),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSummary(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function correrDetalle() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/simulate_once`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cant_ensambladores: Number(cantEnsambladores),
          minutos: Number(minutosDetalle),
          seed: seedDetalle === "" ? null : Number(seedDetalle),
          ...bodyConfig(),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDetail(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const detailRowsFiltradas = useMemo(() => {
    if (!detail?.rows) return [];
    const d = filaDesde === "" ? null : Number(filaDesde);
    const h = filaHasta === "" ? null : Number(filaHasta);

    if (d === null && h === null) return detail.rows;

    return detail.rows.filter((r) => {
      const f = Number(r.fila);
      if (Number.isNaN(f)) return false;
      if (d !== null && f < d) return false;
      if (h !== null && f > h) return false;
      return true;
    });
  }, [detail, filaDesde, filaHasta]);

  return (
    <div style={{ maxWidth: 1300, margin: "24px auto", padding: "0 16px", fontFamily: "Arial, sans-serif" }}>
      <h1 style={{ marginBottom: 8 }}>TP Simulación - Ensambladores y Horno</h1>

      {/* Parámetros globales del modelo */}
      <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 8, marginBottom: 14, background: "#fafafa" }}>
        <div style={{ fontWeight: 700, marginBottom: 10 }}>Parámetros del modelo</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "end" }}>
          <NumberInput label="Ensamble min" value={ensambleMin} onChange={setEnsambleMin} min={0} step="0.01" />
          <NumberInput label="Ensamble max" value={ensambleMax} onChange={setEnsambleMax} min={0} step="0.01" />
          <NumberInput label="Horno min" value={hornoMin} onChange={setHornoMin} min={0} step="0.01" />
          <NumberInput label="Horno max" value={hornoMax} onChange={setHornoMax} min={0} step="0.01" />

          <label style={{ display: "grid", gap: 4 }}>
            <span>Prioridad si coincide fin</span>
            <select value={prioridadEmpate} onChange={(e) => setPrioridadEmpate(e.target.value)}>
              <option value="ensamble">Fin ensamble</option>
              <option value="horno">Fin horno</option>
            </select>
          </label>

          <div style={{ color: "#666", fontSize: 13, maxWidth: 450 }}>
            Ensamble y horno se modelan como uniformes entre min y max. La prioridad de empate permite decidir qué evento se procesa primero cuando ambos ocurren en el mismo reloj.
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button onClick={() => setTab("resumen")} style={{ padding: "8px 12px" }}>
          Resumen (óptimo)
        </button>
        <button onClick={() => setTab("detalle")} style={{ padding: "8px 12px" }}>
          Detalle (tabla de eventos)
        </button>
      </div>

      {error && (
        <div style={{ background: "#ffe5e5", color: "#a00", padding: 10, borderRadius: 6, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {tab === "resumen" && (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "end", marginBottom: 14 }}>
            <NumberInput label="Máx. ensambladores" value={maxEnsambladores} onChange={setMaxEnsambladores} min={1} step="1" />
            <NumberInput label="Repeticiones" value={repeticiones} onChange={setRepeticiones} min={1} step="1" />
            <NumberInput label="Minutos" value={minutosResumen} onChange={setMinutosResumen} min={1} step="1" />
            <NumberInput label="Seed base" value={seedBase} onChange={setSeedBase} step="1" />

            <button onClick={correrResumen} disabled={loading} style={{ height: 34 }}>
              {loading ? "Calculando..." : "Correr resumen"}
            </button>
          </div>

          {summary && (
            <>
              <div style={{ marginBottom: 10, padding: 10, background: "#f6f9ff", borderRadius: 6 }}>
                <strong>Óptimo sugerido:</strong> {summary.optimo} ensambladores
                <br />
                <span style={{ color: "#555" }}>{summary.criterio}</span>
              </div>
              <DataTable columns={summary.columns} rows={summary.rows} />
            </>
          )}
        </>
      )}

      {tab === "detalle" && (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "end", marginBottom: 14 }}>
            <NumberInput label="Cant. ensambladores" value={cantEnsambladores} onChange={setCantEnsambladores} min={1} step="1" />
            <NumberInput label="Minutos" value={minutosDetalle} onChange={setMinutosDetalle} min={1} step="1" />
            <NumberInput label="Seed" value={seedDetalle} onChange={setSeedDetalle} step="1" />

            <button onClick={correrDetalle} disabled={loading} style={{ height: 34 }}>
              {loading ? "Simulando..." : "Correr detalle"}
            </button>
          </div>

          {detail && (
            <>
              <div style={{ marginBottom: 10, padding: 10, background: "#f8fff6", borderRadius: 6 }}>
                <strong>Piezas terminadas:</strong> {detail.cant_piezas} <br />
                <strong>Ensambladores:</strong> {detail.cant_ensambladores} | <strong>Minutos:</strong> {detail.minutos}
              </div>

              {/* Filtro de filas */}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "end", marginBottom: 10 }}>
                <NumberInput label="Fila desde" value={filaDesde} onChange={setFilaDesde} min={0} step="1" />
                <NumberInput label="Fila hasta" value={filaHasta} onChange={setFilaHasta} min={0} step="1" />
                <button
                  onClick={() => {
                    setFilaDesde("");
                    setFilaHasta("");
                  }}
                  style={{ height: 34 }}
                >
                  Limpiar filtro
                </button>
                <div style={{ color: "#666", fontSize: 13 }}>
                  Ejemplo: desde 50 hasta 75 (la fila 0 es la inicialización).
                </div>
              </div>

              <DataTable columns={detail.columns} rows={detailRowsFiltradas} />
            </>
          )}
        </>
      )}
    </div>
  );
}