"use client";
import { useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { clearToken, getRoleFromToken } from "src/lib/auth";
import Link from "next/link";

type LayoutProps = {
  children: ReactNode;
  helpContent?: ReactNode;
};

type MenuItem = {
  href: string;
  label: string;
  icon: string;
};

export function Layout({ children, helpContent }: LayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const role = getRoleFromToken();
  const isAdmin = role === "admin";

  const [profileOpen, setProfileOpen] = useState(false);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  // Dynamic menu based on role
  const menuItems: MenuItem[] = isAdmin
    ? [
        { href: "/admin/dashboard", label: "Dashboard", icon: "🏠" },
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
        { href: "/content", label: "Content", icon: "✍️" },
        { href: "/intelligence", label: "Intelligence", icon: "🧠" },
        { href: "/compliance", label: "Compliance", icon: "✓" },
        { href: "/analytics", label: "Analytics", icon: "📈" },
        { href: "/settings", label: "Settings", icon: "⚙️" },
      ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="h-16 border-b bg-white flex items-center justify-between px-4 sticky top-0 z-50">
        {/* Left: Menu Toggle + Logo */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded"
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6"
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
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">B</span>
              </div>
              <span className="font-bold text-xl">Blitz</span>
            </div>
          </Link>
        </div>

        {/* Right: Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-lg"
          >
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold">
                {role?.charAt(0).toUpperCase()}
              </span>
            </div>
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
              <div className="absolute right-0 mt-2 w-48 bg-white border rounded-lg shadow-lg z-20">
                <div className="p-3 border-b">
                  <p className="text-sm font-semibold capitalize">{role}</p>
                  <p className="text-xs text-gray-500">Role</p>
                </div>
                <Link
                  href="/profile"
                  className="block px-4 py-2 text-sm hover:bg-gray-100"
                  onClick={() => setProfileOpen(false)}
                >
                  Profile
                </Link>
                <Link
                  href="/settings"
                  className="block px-4 py-2 text-sm hover:bg-gray-100"
                  onClick={() => setProfileOpen(false)}
                >
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 border-t"
                >
                  Logout
                </button>
              </div>
            </>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Navigation */}
        <aside
          className={`${
            leftSidebarOpen ? "w-64" : "w-0"
          } transition-all duration-300 border-r bg-white overflow-y-auto`}
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
                        ? "bg-blue-50 text-blue-600 font-semibold"
                        : "hover:bg-gray-100 text-gray-700"
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
        <main className="flex-1 overflow-y-auto bg-gray-50">{children}</main>

        {/* Right Sidebar - Context Help */}
        <aside
          className={`${
            rightSidebarOpen ? "w-80" : "w-0"
          } transition-all duration-300 border-l bg-white overflow-y-auto`}
        >
          {rightSidebarOpen && (
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg">Help</h3>
                <button
                  onClick={() => setRightSidebarOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                  aria-label="Close help"
                >
                  <svg
                    className="w-5 h-5"
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
              <div className="space-y-4">
                {helpContent || (
                  <div className="text-sm text-gray-600">
                    <p className="mb-2">
                      No help content available for this page.
                    </p>
                    <p>
                      Need assistance? Contact{" "}
                      <a
                        href="mailto:support@blitz.com"
                        className="text-blue-600 underline"
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

        {/* Toggle Right Sidebar Button (when closed) */}
        {!rightSidebarOpen && (
          <button
            onClick={() => setRightSidebarOpen(true)}
            className="fixed right-0 top-1/2 -translate-y-1/2 bg-white border border-r-0 rounded-l-lg p-2 shadow-lg hover:bg-gray-50"
            aria-label="Open help"
          >
            <svg
              className="w-5 h-5"
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
