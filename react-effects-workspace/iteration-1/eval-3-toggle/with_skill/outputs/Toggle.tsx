import { useState, useCallback } from "react";

// ============================================================
// Toggle Component
// ============================================================
// Follows the react-effects skill guidance (Scenario 9):
// Do NOT use useEffect to notify parent of state changes.
// Instead, call the parent's onChange callback in the same
// event handler that updates local state. React batches both
// setState calls into a single render pass.
// ============================================================

interface ToggleProps {
  /** Callback invoked with the new toggle value whenever it changes */
  onChange: (isOn: boolean) => void;
  /** Optional initial state (defaults to false / off) */
  initialOn?: boolean;
  /** Optional label displayed next to the toggle */
  label?: string;
}

function Toggle({ onChange, initialOn = false, label }: ToggleProps) {
  const [isOn, setIsOn] = useState(initialOn);

  // RIGHT pattern (from skill Scenario 9):
  // Update local state AND notify parent in the same event handler.
  // React batches both updates into a single render — no extra
  // render cycle, no unpredictable update order.
  function handleClick() {
    const nextIsOn = !isOn;
    setIsOn(nextIsOn);
    onChange(nextIsOn); // Parent is notified in the same event batch
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isOn}
      onClick={handleClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        padding: "8px 16px",
        border: "2px solid",
        borderColor: isOn ? "#22c55e" : "#d1d5db",
        borderRadius: "9999px",
        backgroundColor: isOn ? "#22c55e" : "#e5e7eb",
        color: isOn ? "#fff" : "#374151",
        cursor: "pointer",
        fontSize: "14px",
        fontWeight: 500,
        transition: "all 0.2s ease",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: "20px",
          height: "20px",
          borderRadius: "50%",
          backgroundColor: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
          transform: isOn ? "translateX(4px)" : "translateX(-4px)",
          transition: "transform 0.2s ease",
        }}
      />
      {label && <span>{label}</span>}
    </button>
  );
}

// ============================================================
// Parent Component
// ============================================================
// Demonstrates how the parent receives toggle state changes
// through the onChange callback — no useEffect involved.
// ============================================================

function ParentComponent() {
  const [isToggleOn, setIsToggleOn] = useState(false);

  // This handler is called directly by Toggle's event handler,
  // NOT by a useEffect reacting to state changes.
  const handleToggleChange = useCallback((isOn: boolean) => {
    setIsToggleOn(isOn);
  }, []);

  return (
    <div style={{ padding: "24px", fontFamily: "sans-serif" }}>
      <h2>Toggle Demo</h2>

      <div style={{ marginBottom: "16px" }}>
        <Toggle
          onChange={handleToggleChange}
          label="Enable notifications"
        />
      </div>

      <div
        style={{
          padding: "16px",
          borderRadius: "8px",
          backgroundColor: isToggleOn ? "#f0fdf4" : "#fef2f2",
          border: `1px solid ${isToggleOn ? "#bbf7d0" : "#fecaca"}`,
          color: isToggleOn ? "#166534" : "#991b1b",
          transition: "all 0.2s ease",
        }}
      >
        <p style={{ margin: 0 }}>
          Notifications are currently{" "}
          <strong>{isToggleOn ? "ON" : "OFF"}</strong>
        </p>
      </div>
    </div>
  );
}

export { Toggle, ParentComponent };
export default ParentComponent;
