"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSun, faMoon } from "@fortawesome/free-solid-svg-icons";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <Button variant="ghost" size="icon" className="w-10 h-10 rounded-full" />;
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="w-10 h-10 rounded-full bg-white/5 border border-white/10 hover:bg-primary/20 hover:text-primary transition-all duration-300"
    >
      {theme === "dark" ? (
        <FontAwesomeIcon icon={faSun} className="w-4 h-4 text-yellow-400" />
      ) : (
        <FontAwesomeIcon icon={faMoon} className="w-4 h-4 text-blue-600" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
