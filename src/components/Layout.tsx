// src/components/Layout.tsx
"use client";
import { useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { clearToken, getRoleFromToken, getUserFromToken } from "src/lib/auth";
import { api } from "src/lib/appClient";
import { useTheme } from "src/contexts/ThemeContext";
import { getHelpContent } from "src/config/helpContent";
import Link from "next/link";

type LayoutProps = {
  children: ReactNode;
};

type MenuItem = {
  href: string;
  label: string;
  icon: string;
};

type UserInfo = {
  email: string;
  role: string;
};

export default function Layout({ children }: LayoutProps) {
  // All hooks must be called at the top level, before any conditional returns
  const router = useRouter();
  const pathname = usePathname();
  const { theme } = useTheme();
  const role = getRoleFromToken();
  const isAdmin = role === "admin";

  const [profileOpen, setProfileOpen] = useState(false);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);

  // Check if current page is an auth page (login, register)
  const isAuthPage = pathname === "/login" || pathname === "/register";

  // Get help content based on current pathname
  const helpContent = getHelpContent(pathname);

  // Fetch user info on mount (only if token exists)
  useEffect(() => {
    let mounted = true;
    const fetchUserInfo = async () => {
      // Check if token exists before making API call
      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;

      if (!token) {
        // No token, set default user info from token parsing
        if (mounted && role) {
          setUserInfo({ email: "User", role: role });
        }
        return;
      }

      try {
        const res = await api.get("/api/auth/me");
        if (mounted) setUserInfo(res.data);
      } catch (err) {
        // Only log error if we actually have a token (prevents noise on login page)
        if (token) {
          console.error("Failed to fetch user info:", err);
        }
        if (mounted && role) {
          setUserInfo({ email: "User", role: role });
        }
      }
    };
    fetchUserInfo();
    return () => {
      mounted = false;
    };
  }, [role]);

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  const menuItems: MenuItem[] = isAdmin
    ? [
        { href: "/admin/dashboard", label: "Dashboard", icon: "🏠" },
        { href: "/admin/campaigns", label: "Campaigns", icon: "📢" },
        { href: "/products", label: "Product Library", icon: "📦" },
        { href: "/admin/tools", label: "Admin Tools", icon: "🔧" },
        { href: "/admin/ai_router", label: "AI Router", icon: "🤖" },
        { href: "/admin/users", label: "Users", icon: "👥" },
        { href: "/admin/settings", label: "Settings", icon: "⚙️" },
        { href: "/admin/analytics", label: "Analytics", icon: "📊" },
        { href: "/admin/compliance", label: "Compliance", icon: "🛡️" },
        { href: "/admin/api-keys", label: "API Keys", icon: "🔑" },
      ]
    : [
        { href: "/dashboard", label: "Dashboard", icon: "🏠" },
        { href: "/campaigns", label: "Campaigns", icon: "📢" },
        { href: "/products", label: "Product Library", icon: "📦" },
        { href: "/content", label: "Content", icon: "✍️" },
        { href: "/intelligence", label: "Intelligence", icon: "🧠" },
        { href: "/compliance", label: "Compliance", icon: "✓" },
        { href: "/analytics", label: "Analytics", icon: "📈" },
        { href: "/settings", label: "Settings", icon: "⚙️" },
      ];

  if (typeof window !== "undefined") {
    // debug log to verify single render — remove after verification
    // eslint-disable-next-line no-console
    console.debug("[Layout] render");
  }

  // If auth page, render children without layout chrome
  // This comes AFTER all hooks to avoid violating Rules of Hooks
  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    // Use the same background for the shell and page canvas so the main page matches the sidebar
    <div className="min-h-screen flex flex-col bg-[var(--bg-secondary)]">
      {/* Header */}
      <header className="h-16 border-b border-[var(--border-color)] bg-[var(--bg-primary)] flex items-center justify-between px-4 sticky top-0 z-50">
        {/* Left: Menu Toggle + Logo */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
            className="p-2 hover:bg-[var(--hover-bg)] rounded"
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6 text-[var(--text-primary)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <Link href={isAdmin ? "/admin/dashboard" : "/dashboard"}>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">B</span>
              </div>
              <span className="font-bold text-xl text-[var(--text-primary)]">
                Blitz
              </span>
            </div>
          </Link>
        </div>

        {/* Right: User Info + Profile Dropdown */}
        <div className="flex items-center space-x-4">
          {userInfo && (
            <div className="hidden md:flex flex-col items-end">
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                {userInfo.email}
              </span>
              <span className="text-xs text-[var(--text-secondary)] capitalize">
                {userInfo.role}
              </span>
            </div>
          )}

          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center space-x-2 p-2 hover:bg-[var(--hover-bg)] rounded-lg"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-white">
                  {userInfo?.email?.charAt(0).toUpperCase() || "U"}
                </span>
              </div>
              <svg
                className="w-4 h-4 text-[var(--text-primary)]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {profileOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setProfileOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-64 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg shadow-lg z-20">
                  <div className="p-3 border-b border-[var(--border-color)]">
                    <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                      {userInfo?.email || "Loading..."}
                    </p>
                    <p className="text-xs text-[var(--text-secondary)] capitalize">
                      {userInfo?.role || "user"}
                    </p>
                  </div>
                  <Link
                    href="/profile"
                    className="block px-4 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
                    onClick={() => setProfileOpen(false)}
                  >
                    Profile
                  </Link>
                  <Link
                    href="/settings"
                    className="block px-4 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
                    onClick={() => setProfileOpen(false)}
                  >
                    Settings
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-[var(--hover-bg)] border-t border-[var(--border-color)]"
                  >
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className={`${
            leftSidebarOpen ? "w-64" : "w-0"
          } transition-all duration-300 border-r border-[var(--border-color)] bg-[var(--bg-primary)] overflow-y-auto`}
        >
          {leftSidebarOpen && (
            <nav className="p-4 space-y-1">
              {menuItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href as any}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold"
                        : "hover:bg-[var(--hover-bg)] text-[var(--text-primary)]"
                    }`}
                  >
                    <span className="text-xl">{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-[var(--bg-secondary)]">
          {children}
        </main>

        {/* Right Sidebar */}
        <aside
          className={`${
            rightSidebarOpen ? "w-80" : "w-0"
          } transition-all duration-300 border-l border-[var(--border-color)] bg-[var(--bg-sidebar-help)] overflow-y-auto`}
        >
          {rightSidebarOpen && (
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg text-[var(--text-primary)]">
                  Help
                </h3>
                <button
                  onClick={() => setRightSidebarOpen(false)}
                  className="p-1 hover:bg-[var(--hover-bg)] rounded"
                  aria-label="Close help"
                >
                  <svg
                    className="w-5 h-5 text-[var(--text-primary)]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <div className="space-y-4 text-[var(--text-secondary)]">
                {helpContent ? (
                  <div className="text-sm space-y-4">
                    {/* Title and Description */}
                    <div>
                      <h4 className="font-semibold text-lg text-[var(--text-primary)] mb-2">
                        {helpContent.title}
                      </h4>
                      <p className="text-[var(--text-secondary)] leading-relaxed">
                        {helpContent.description}
                      </p>
                    </div>

                    {/* Steps Section */}
                    {helpContent.steps && helpContent.steps.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-[var(--text-primary)] mb-3 flex items-center space-x-2">
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                            />
                          </svg>
                          <span>Steps to Complete</span>
                        </h5>
                        <div className="space-y-3">
                          {helpContent.steps.map((step) => (
                            <div
                              key={step.number}
                              className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
                            >
                              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                                {step.number}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h6 className="font-semibold text-[var(--text-primary)] mb-1">
                                  {step.title}
                                </h6>
                                <p className="text-[var(--text-secondary)] text-xs leading-relaxed">
                                  {step.description}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Tips Section */}
                    {helpContent.tips && helpContent.tips.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-[var(--text-primary)] mb-2 flex items-center space-x-2">
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                            />
                          </svg>
                          <span>Pro Tips</span>
                        </h5>
                        <ul className="space-y-2">
                          {helpContent.tips.map((tip, index) => (
                            <li
                              key={index}
                              className="flex items-start space-x-2 text-[var(--text-secondary)]"
                            >
                              <span className="text-blue-500 mt-0.5 font-bold">
                                •
                              </span>
                              <span className="leading-relaxed">{tip}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Links Section */}
                    {helpContent.links && helpContent.links.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-[var(--text-primary)] mb-2">
                          Related Resources
                        </h5>
                        <ul className="space-y-2">
                          {helpContent.links.map((link, index) => (
                            <li key={index}>
                              <a
                                href={link.href}
                                className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                              >
                                {link.label} →
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm">
                    <p className="mb-2">
                      No help content available for this page.
                    </p>
                    <p>
                      Need assistance? Contact{" "}
                      <a
                        href="mailto:support@blitz.com"
                        className="text-blue-600 dark:text-blue-400 underline"
                      >
                        support@blitz.com
                      </a>
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </aside>

        {!rightSidebarOpen && (
          <button
            onClick={() => setRightSidebarOpen(true)}
            className="fixed right-0 top-1/2 -translate-y-1/2 bg-[var(--bg-primary)] border border-r-0 border-[var(--border-color)] rounded-l-lg p-2 shadow-lg hover:bg-[var(--hover-bg)]"
            aria-label="Open help"
          >
            <svg
              className="w-5 h-5 text-[var(--text-primary)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
