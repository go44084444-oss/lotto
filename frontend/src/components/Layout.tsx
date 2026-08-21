import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="layout">
      <header className="nav">
        <Link to="/" className="brand">
          로또 조합 배분
        </Link>
        {isAuthenticated && (
          <nav>
            <Link to="/">이번 주 배정</Link>
            <Link to="/win-check">당첨 확인</Link>
            <button onClick={handleLogout}>로그아웃</button>
          </nav>
        )}
      </header>
      <main>{children}</main>
    </div>
  );
}
