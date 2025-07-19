import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './auth/Login';
import Register from './auth/Register';
import Dashboard from './dashboard/Dashboard';
import Assessment from './assessment/Assessment';


export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/" element={

            <Dashboard />

          } />
          <Route path="/assessment" element={

            <Assessment />

          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}