import type { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LogoMark } from "./Logo";

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
          <LogoMark />
          LottoTree
        </Link>
        {isAuthenticated && (
          <nav>
            <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
              이번 주 배정
            </NavLink>
            <NavLink to="/win-check" className={({ isActive }) => (isActive ? "active" : "")}>
              당첨 확인
            </NavLink>
            <NavLink to="/draws" className={({ isActive }) => (isActive ? "active" : "")}>
              지난 회차
            </NavLink>
            <button onClick={handleLogout}>로그아웃</button>
          </nav>
        )}
      </header>
      <main>{children}</main>
    </div>
  );
}
