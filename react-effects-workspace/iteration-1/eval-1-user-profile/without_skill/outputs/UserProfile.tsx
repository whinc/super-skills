import { useState, useMemo, useEffect } from "react";

interface UserProfileProps {
  userId: string;
  firstName: string;
  lastName: string;
}

export default function UserProfile({
  userId,
  firstName,
  lastName,
}: UserProfileProps) {
  const [comment, setComment] = useState("");

  // Reset the comment input when userId changes
  useEffect(() => {
    setComment("");
  }, [userId]);

  // Derive full name from firstName and lastName
  const fullName = useMemo(
    () => `${firstName} ${lastName}`,
    [firstName, lastName],
  );

  return (
    <div className="user-profile">
      <h2>{fullName}</h2>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Write a comment..."
      />
    </div>
  );
}
