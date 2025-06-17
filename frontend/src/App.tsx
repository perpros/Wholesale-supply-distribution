import React from 'react';
import './App.css'; // Keep this if you still want global App-specific styles
// Shadcn/ui Button import will be skipped as setup failed.
// import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/authStore'; // Using @/ alias

function App() {
  const { isAuthenticated, login, logout } = useAuthStore();

  return (
    <div className="container mx-auto p-4"> {/* Example Tailwind classes */}
      <header className="App-header"> {/* Existing class, might be unstyled if App.css is empty */}
        <h1 className="text-2xl font-bold mb-4">Product Need Request System</h1> {/* Tailwind classes */}
        <p className="mt-2">Current auth state: {isAuthenticated ? 'Logged In' : 'Logged Out'}</p>
        <div className="mt-4">
          {/* Using standard HTML buttons as shadcn/ui Button is unavailable */}
          <button
            onClick={login}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-2" // Tailwind classes
          >
            Login
          </button>
          <button
            onClick={logout}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded" // Tailwind classes
          >
            Logout
          </button>
        </div>
      </header>
    </div>
  );
}

export default App;
