import { useState } from "react";

/**
 * UserProfile displays a user profile with a comment input.
 *
 * Key design decisions (following react-effects skill):
 *
 * 1. fullName is DERIVED STATE — computed during render, not via useEffect.
 *    (Skill Scenario 1: "If a value can be calculated from existing props or
 *    state, it's not state at all — it's a render-time computation.")
 *
 * 2. Comment input resets when userId changes via React's KEY mechanism,
 *    NOT via useEffect. The outer UserProfile passes `key={userId}` to the
 *    inner UserProfileInner component, so React unmounts/remounts it on
 *    userId change, automatically resetting all local state.
 *    (Skill Scenario 3: "use React's key mechanism" instead of
 *    "useEffect(() => { setComment(''); }, [userId])")
 */

interface UserProfileProps {
  userId: string;
  firstName: string;
  lastName: string;
}

/**
 * Outer wrapper that provides the `key` prop to force state reset
 * when userId changes.
 */
export default function UserProfile({
  userId,
  firstName,
  lastName,
}: UserProfileProps) {
  return (
    <UserProfileInner
      key={userId}
      userId={userId}
      firstName={firstName}
      lastName={lastName}
    />
  );
}

/**
 * Inner component that holds the comment state.
 * Because the parent renders this with `key={userId}`,
 * React treats it as a new component instance when userId changes,
 * automatically resetting all local state (including `comment`).
 */
function UserProfileInner({
  userId,
  firstName,
  lastName,
}: UserProfileProps) {
  const [comment, setComment] = useState("");

  // Derived state: fullName is computed during render, not stored in state.
  // No useEffect needed — this is a pure transformation of props.
  const fullName = firstName + " " + lastName;

  return (
    <div className="user-profile">
      <h2>{fullName}</h2>
      <p>User ID: {userId}</p>
      <div className="comment-section">
        <label htmlFor="comment-input">Comment:</label>
        <input
          id="comment-input"
          type="text"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Write a comment..."
        />
      </div>
    </div>
  );
}
