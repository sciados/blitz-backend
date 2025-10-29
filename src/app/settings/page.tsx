"use client";
import { AuthGate } from "src/components/AuthGate";
import { useTheme } from "src/contexts/ThemeContext";

const helpContent = {
  title: "Content Generation",
  description: "Generate AI-powered content for your campaigns.",
  tips: [
    "Select content type (email, ad, social post)",
    "Customize tone and brand voice",
    "Save generated content to campaigns",
    "Regenerate if results don't match expectations",
  ],
};

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <AuthGate requiredRole="user" helpContent={helpContent}>
      <div className="p-6 max-w-4xl">
        <h1 className="text-3xl font-bold mb-2 text-[var(--text-primary)]">
          Settings
        </h1>
        <p className="text-[var(--text-secondary)] mb-6">
          Manage your account and preferences
        </p>

        {/* Appearance Section */}
        <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
            Appearance
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-3 text-[var(--text-primary)]">
                Theme
              </label>
              <div className="grid grid-cols-2 gap-4">
                {/* Light Theme Option */}
                <button
                  onClick={() => setTheme("light")}
                  className={`p-4 border-2 rounded-lg transition-all ${
                    theme === "light"
                      ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20"
                      : "border-[var(--border-color)] hover:border-gray-400"
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-white border-2 border-gray-300 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-6 h-6 text-yellow-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                        />
                      </svg>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-[var(--text-primary)]">
                        Light
                      </p>
                      <p className="text-xs text-[var(--text-secondary)]">
                        Bright and clean
                      </p>
                    </div>
                  </div>
                  {theme === "light" && (
                    <div className="mt-2 flex items-center text-blue-600 text-sm">
                      <svg
                        className="w-4 h-4 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Active
                    </div>
                  )}
                </button>

                {/* Dark Theme Option */}
                <button
                  onClick={() => setTheme("dark")}
                  className={`p-4 border-2 rounded-lg transition-all ${
                    theme === "dark"
                      ? "border-blue-600 bg-blue-50 dark:bg-blue-900/20"
                      : "border-[var(--border-color)] hover:border-gray-400"
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gray-900 border-2 border-gray-700 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-6 h-6 text-blue-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                        />
                      </svg>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-[var(--text-primary)]">
                        Dark
                      </p>
                      <p className="text-xs text-[var(--text-secondary)]">
                        Easy on the eyes
                      </p>
                    </div>
                  </div>
                  {theme === "dark" && (
                    <div className="mt-2 flex items-center text-blue-600 dark:text-blue-400 text-sm">
                      <svg
                        className="w-4 h-4 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Active
                    </div>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Other Settings Sections */}
        <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
            Account
          </h2>
          <p className="text-[var(--text-secondary)]">
            Additional account settings coming soon...
          </p>
        </div>
      </div>
    </AuthGate>
  );
}
