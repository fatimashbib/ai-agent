import React, { useState, useEffect } from 'react';
import Recommendation from './Recommendation';

export default function Dashboard() {
  const [userData, setUserData] = useState(null);

  useEffect(() => {
    // Fetch user data when component mounts
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/auth/me', {
          credentials: 'include'
        });
        if (response.ok) {
          setUserData(await response.json());
        }
      } catch (err) {
        console.error('Failed to fetch user data');
      }
    };
    fetchData();
  }, []);

  return (
    <div>
      <h1>Welcome {userData?.email || 'User'}!</h1>
      <Recommendation />
    </div>
  );
}