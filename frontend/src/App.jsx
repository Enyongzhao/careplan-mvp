import { useState, useRef } from "react"

const API_URL = "http://localhost:8000"
const POLL_INTERVAL_MS = 3000

export default function App() {
  const [form, setForm] = useState({
    patient_first_name: "",
    patient_last_name: "",
    mrn: "",
    medication_name: "",
    primary_diagnosis: "",
    patient_records: "",
  })

  const [submitting, setSubmitting] = useState(false)
  const [pollStatus, setPollStatus] = useState(null)   // null | 'pending' | 'processing' | 'completed' | 'failed'
  const [careplan, setCareplan] = useState(null)        // { content } when completed/failed
  const intervalRef = useRef(null)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  function stopPolling() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  function startPolling(careplanId) {
    intervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/careplan/${careplanId}/status/`)
        const data = await res.json()

        setPollStatus(data.status)

        if (data.status === "completed" || data.status === "failed") {
          stopPolling()
          setCareplan({ content: data.content })
        }
      } catch {
        // network blip — keep polling
      }
    }, POLL_INTERVAL_MS)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setPollStatus(null)
    setCareplan(null)
    stopPolling()

    try {
      const res = await fetch(`${API_URL}/api/orders/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      setPollStatus("pending")
      startPolling(data.careplan_id)
    } catch {
      setPollStatus("failed")
      setCareplan({ content: "Network error — could not submit form." })
    } finally {
      setSubmitting(false)
    }
  }

  const isPolling = pollStatus === "pending" || pollStatus === "processing"

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h1>CarePlan Generator</h1>

      <form onSubmit={handleSubmit}>
        <div style={{ display: "grid", gap: 12 }}>
          <input
            name="patient_first_name"
            placeholder="Patient First Name"
            value={form.patient_first_name}
            onChange={handleChange}
            style={inputStyle}
          />
          <input
            name="patient_last_name"
            placeholder="Patient Last Name"
            value={form.patient_last_name}
            onChange={handleChange}
            style={inputStyle}
          />
          <input
            name="mrn"
            placeholder="MRN (6-digit)"
            value={form.mrn}
            onChange={handleChange}
            style={inputStyle}
          />
          <input
            name="medication_name"
            placeholder="Medication Name"
            value={form.medication_name}
            onChange={handleChange}
            style={inputStyle}
          />
          <input
            name="primary_diagnosis"
            placeholder="Primary Diagnosis (ICD-10)"
            value={form.primary_diagnosis}
            onChange={handleChange}
            style={inputStyle}
          />
          <textarea
            name="patient_records"
            placeholder="Patient Records / Medical History"
            value={form.patient_records}
            onChange={handleChange}
            rows={5}
            style={inputStyle}
          />
          <button type="submit" disabled={submitting || isPolling} style={buttonStyle}>
            {submitting ? "Submitting..." : "Generate Care Plan"}
          </button>
        </div>
      </form>

      {/* Polling status */}
      {isPolling && (
        <div style={{ marginTop: 32, color: "#555" }}>
          <p>
            Status: <strong>{pollStatus}</strong>
            {"  "}
            <span style={{ animation: "none" }}>⏳ Checking every 3 s...</span>
          </p>
        </div>
      )}

      {/* Completed */}
      {pollStatus === "completed" && careplan && (
        <div style={{ marginTop: 32 }}>
          <p>Status: <strong style={{ color: "#16a34a" }}>completed</strong></p>
          <div style={{
            background: "#f5f5f5",
            padding: 20,
            borderRadius: 8,
            whiteSpace: "pre-wrap",
            lineHeight: 1.6,
          }}>
            {careplan.content}
          </div>
        </div>
      )}

      {/* Failed */}
      {pollStatus === "failed" && (
        <div style={{ marginTop: 32 }}>
          <p>Status: <strong style={{ color: "#dc2626" }}>failed</strong></p>
          <div style={{ color: "#dc2626" }}>
            {careplan?.content || "An error occurred."}
          </div>
        </div>
      )}
    </div>
  )
}

const inputStyle = {
  padding: "10px 12px",
  fontSize: 14,
  border: "1px solid #ddd",
  borderRadius: 6,
  width: "100%",
  boxSizing: "border-box",
}

const buttonStyle = {
  padding: "12px 24px",
  background: "#2563eb",
  color: "white",
  border: "none",
  borderRadius: 6,
  fontSize: 16,
  cursor: "pointer",
}
