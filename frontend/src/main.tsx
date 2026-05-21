import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";
import "./index.css";

const queryClient = new QueryClient();

// Limpieza one-shot de token persistido por versión anterior (pre-fix A1).
// Esta línea puede eliminarse 30 días después del deploy de este cambio.
try {
  localStorage.removeItem("auth-storage");
} catch {
  // ignorar — algunos navegadores con storage deshabilitado tiran al acceder
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
