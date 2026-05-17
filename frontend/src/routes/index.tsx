import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Login } from "@/pages/Login";

const Dashboard = lazy(() =>
  import("@/pages/Dashboard").then((m) => ({ default: m.Dashboard }))
);

const Usuarios = lazy(() =>
  import("@/pages/Usuarios").then((m) => ({ default: m.Usuarios }))
);

const Bancos = lazy(() =>
  import("@/pages/Bancos").then((m) => ({ default: m.Bancos }))
);

const Destinatarios = lazy(() =>
  import("@/pages/Destinatarios").then((m) => ({ default: m.Destinatarios }))
);

const XmlIngreso = lazy(() =>
  import("@/pages/XmlIngreso").then((m) => ({ default: m.XmlIngreso }))
);

const XmlLista = lazy(() =>
  import("@/pages/XmlLista").then((m) => ({ default: m.XmlLista }))
);

const XmlPendientes = lazy(() =>
  import("@/pages/XmlPendientes").then((m) => ({ default: m.XmlPendientes }))
);

const KardexPage = lazy(() =>
  import("@/pages/Kardex").then((m) => ({ default: m.Kardex }))
);

const EntregasPage = lazy(() =>
  import("@/pages/Entregas").then((m) => ({ default: m.Entregas }))
);

const EntregaNuevaPage = lazy(() =>
  import("@/pages/EntregaNueva").then((m) => ({ default: m.EntregaNueva }))
);

const EntregaDetallePage = lazy(() =>
  import("@/pages/EntregaDetalle").then((m) => ({ default: m.EntregaDetalle }))
);

const fallback = <div>Cargando...</div>;

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            path: "dashboard",
            element: <Suspense fallback={fallback}><Dashboard /></Suspense>,
          },
          {
            path: "usuarios",
            element: <Suspense fallback={fallback}><Usuarios /></Suspense>,
          },
          {
            path: "bancos",
            element: <Suspense fallback={fallback}><Bancos /></Suspense>,
          },
          {
            path: "destinatarios",
            element: <Suspense fallback={fallback}><Destinatarios /></Suspense>,
          },
          {
            path: "xml",
            children: [
              {
                path: "pendientes",
                element: <ProtectedRoute roles={["admin", "operador"]} />,
                children: [
                  {
                    index: true,
                    element: <Suspense fallback={fallback}><XmlPendientes /></Suspense>,
                  },
                ],
              },
              {
                path: "ingreso",
                element: <ProtectedRoute roles={["admin", "operador"]} />,
                children: [
                  {
                    index: true,
                    element: <Suspense fallback={fallback}><XmlIngreso /></Suspense>,
                  },
                ],
              },
              {
                path: "lista",
                element: <ProtectedRoute roles={["admin", "operador", "lectura"]} />,
                children: [
                  {
                    index: true,
                    element: <Suspense fallback={fallback}><XmlLista /></Suspense>,
                  },
                ],
              },
            ],
          },
          {
            path: "kardex",
            element: <ProtectedRoute roles={["admin", "operador", "lectura"]} />,
            children: [
              {
                index: true,
                element: <Suspense fallback={fallback}><KardexPage /></Suspense>,
              },
            ],
          },
          {
            path: "entregas",
            children: [
              {
                element: <ProtectedRoute roles={["admin", "operador", "lectura"]} />,
                children: [
                  {
                    index: true,
                    element: <Suspense fallback={fallback}><EntregasPage /></Suspense>,
                  },
                  {
                    path: ":id",
                    element: <Suspense fallback={fallback}><EntregaDetallePage /></Suspense>,
                  },
                ],
              },
              {
                element: <ProtectedRoute roles={["admin", "operador"]} />,
                children: [
                  {
                    path: "nueva",
                    element: <Suspense fallback={fallback}><EntregaNuevaPage /></Suspense>,
                  },
                ],
              },
            ],
          },
          {
            index: true,
            element: <Navigate to="/dashboard" replace />,
          },
          {
            path: "*",
            element: <Navigate to="/dashboard" replace />,
          },
        ],
      },
    ],
  },
]);
