import React, { useState } from "react";

export default function Predict() {
  const [features, setFeatures] = useState("");
  const [result, setResult] = useState(null);

  const handlePredict = async (endpoint) => {
    const res = await fetch(`http://localhost:5000/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ features: features.split(",").map(Number) }),
    });
    const data = await res.json();
    setResult(data);
  };

  return (
    <div>
      <h2>Prediction</h2>
      <input
        value={features}
        onChange={(e) => setFeatures(e.target.value)}
        placeholder="Enter features comma-separated"
      />
      <button onClick={() => handlePredict("predict-churn")}>Churn</button>
      <button onClick={() => handlePredict("predict-rf")}>Random Forest</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
