import React, { useState } from "react";

export default function Signup() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    role: "END_USER",
    username: "",
    password: ""
  });

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async () => {
    const res = await fetch("http://localhost:5000/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    alert(JSON.stringify(data));
  };

  return (
    <div>
      <h2>Signup</h2>
      {Object.keys(form).map((key) => (
        <input
          key={key}
          name={key}
          value={form[key]}
          onChange={handleChange}
          placeholder={key}
          style={{ display: "block", margin: "5px" }}
        />
      ))}
      <button onClick={handleSubmit}>Signup</button>
    </div>
  );
}
