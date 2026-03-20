import { useState, useCallback } from "react";

// ─── Toggle Component ────────────────────────────────────────────────
interface ToggleProps {
  /** Optional: controlled initial state */
  defaultOn?: boolean;
  /** Callback fired whenever the toggle state changes */
  onToggle?: (isOn: boolean) => void;
}

function Toggle({ defaultOn = false, onToggle }: ToggleProps) {
  const [isOn, setIsOn] = useState(defaultOn);

  const handleClick = useCallback(() => {
    setIsOn((prev) => {
      const next = !prev;
      onToggle?.(next);
      return next;
    });
  }, [onToggle]);

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isOn}
      onClick={handleClick}
      className={`
        relative inline-flex h-7 w-12 shrink-0 cursor-pointer items-center
        rounded-full border-2 border-transparent transition-colors
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
        ${isOn ? "bg-primary" : "bg-muted"}
      `}
    >
      <span
        className={`
          pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg
          ring-0 transition-transform
          ${isOn ? "translate-x-5" : "translate-x-0.5"}
        `}
      />
    </button>
  );
}

// ─── Parent Component ────────────────────────────────────────────────
function ToggleDemo() {
  const [notifications, setNotifications] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  return (
    <div className="mx-auto max-w-sm space-y-6 p-6">
      <h2 className="text-lg font-semibold">Settings</h2>

      {/* Notifications toggle */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Notifications</p>
          <p className="text-xs text-muted-foreground">
            {notifications ? "Enabled" : "Disabled"}
          </p>
        </div>
        <Toggle onToggle={setNotifications} />
      </div>

      {/* Dark mode toggle */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Dark Mode</p>
          <p className="text-xs text-muted-foreground">
            {darkMode ? "On" : "Off"}
          </p>
        </div>
        <Toggle onToggle={setDarkMode} />
      </div>

      {/* Status display reacting to toggle state */}
      <div className="rounded-md border p-3 text-sm">
        <p>
          Notifications: <strong>{notifications ? "ON" : "OFF"}</strong>
        </p>
        <p>
          Dark Mode: <strong>{darkMode ? "ON" : "OFF"}</strong>
        </p>
      </div>
    </div>
  );
}

export { Toggle, ToggleDemo };
export default ToggleDemo;
