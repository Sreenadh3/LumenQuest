import React, { useState } from "react";
import Signup from "./components/signup";
import Login from "./components/Login";
import Plans from "./components/Plans";
import Subscribe from "./components/Subscribe";
import Predict from "./components/Predict";

function App() {
  const [token, setToken] = useState(null);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Telecom App</h1>

      {!token ? (
        <>
          <Signup />
          <Login onLogin={setToken} />
        </>
      ) : (
        <>
          <p>✅ Logged in</p>
          <Plans token={token} />
          <Subscribe token={token} />
          <Predict />
        </>
      )}
    </div>
  );
}

export default App;
