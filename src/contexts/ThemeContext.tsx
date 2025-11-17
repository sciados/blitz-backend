"use client";
import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";

type Theme = "light" | "dark";

type ThemeContextType = {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  // Load theme from localStorage or default to dark theme
  useEffect(() => {
    const savedTheme = (typeof window !== "undefined" &&
      localStorage.getItem("theme")) as Theme | null;
    if (savedTheme) {
      setThemeState(savedTheme);
    } else {
      // Always default to dark theme
      setThemeState("dark");
    }
    setMounted(true);
  }, []);

  // Apply theme to document root: data-theme and Tailwind 'dark' class
  useEffect(() => {
    if (!mounted) return;

    // Set data-theme attribute for CSS variable rules
    document.documentElement.setAttribute("data-theme", theme);

    // Ensure Tailwind dark utilities work (darkMode: "class")
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    } else {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
    }

    try {
      localStorage.setItem("theme", theme);
    } catch {
      // ignore storage errors in privacy-mode
    }
  }, [theme, mounted]);

  const toggleTheme = () => {
    setThemeState((prev) => (prev === "light" ? "dark" : "light"));
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  // Prevent flash of unstyled content
  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
