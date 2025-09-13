import React, { useState } from "react";

export default function Subscribe({ token }) {
  const [planId, setPlanId] = useState("");

  const handleSubscribe = async () => {
    const res = await fetch("http://localhost:5000/subscriptions/subscribe", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ plan_id: parseInt(planId), duration_days: 30 }),
    });
    const data = await res.json();
    alert(JSON.stringify(data));
  };

  return (
    <div>
      <h2>Subscribe</h2>
      <input
        value={planId}
        onChange={(e) => setPlanId(e.target.value)}
        placeholder="Plan ID"
      />
      <button onClick={handleSubscribe}>Subscribe</button>
    </div>
  );
}
