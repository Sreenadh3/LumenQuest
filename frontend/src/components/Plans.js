import React, { useEffect, useState } from "react";

export default function Plans({ token }) {
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/plans")
      .then((res) => res.json())
      .then(setPlans);
  }, []);

  return (
    <div>
      <h2>Plans</h2>
      <ul>
        {plans.map((p) => (
          <li key={p.plan_id}>
            {p.name} - ${p.monthly_price} ({p.monthly_quota_gb}GB)
          </li>
        ))}
      </ul>
    </div>
  );
}
