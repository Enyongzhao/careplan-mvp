import { useState } from "react"

const API_URL = "http://localhost:8000"

export default function App() {
  const [form, setForm] = useState({
    patient_first_name: "",
    patient_last_name: "",
    mrn: "",
    medication_name: "",
    primary_diagnosis: "",
    patient_records: "",
  })

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      // POST 提交患者信息
      // 因为是 sync，这个请求会等 LLM 生成完才返回
      const response = await fetch(`${API_URL}/api/orders/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      })
      const data = await response.json()
      setResult(data)
    } catch (err) {
      setResult({ status: "failed", content: "Network error" })
    } finally {
      setLoading(false)
    }
  }

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
          <button
            type="submit"
            disabled={loading}
            style={buttonStyle}
          >
            {loading ? "Generating Care Plan... (please wait)" : "Generate Care Plan"}
          </button>
        </div>
      </form>

      {/* 结果展示 */}
      {result && (
        <div style={{ marginTop: 32 }}>
          <p>Status: <strong>{result.status}</strong></p>

          {result.status === "completed" && (
            <div style={{
              background: "#f5f5f5",
              padding: 20,
              borderRadius: 8,
              whiteSpace: "pre-wrap",
              lineHeight: 1.6
            }}>
              {result.content}
            </div>
          )}

          {result.status === "failed" && (
            <div style={{ color: "red" }}>
              Error: {result.content}
            </div>
          )}
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