import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WinCheckPage } from "./pages/WinCheckPage";

export default function App() {
  return (
    <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/win-check"
            element={
              <ProtectedRoute>
                <WinCheckPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </AuthProvider>
  );
}
