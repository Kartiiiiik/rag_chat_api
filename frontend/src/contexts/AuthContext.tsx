import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ error?: string }>;
  signup: (email: string, password: string, name: string) => Promise<{ error?: string }>;
  loginWithGoogle: () => Promise<{ error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'rag_chat_user';
const TOKEN_KEY = 'rag_chat_token';
const API_URL = 'http://localhost:8000'; // Adjust if needed

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (token) {
      if (stored) {
        try {
          setUser(JSON.parse(stored));
        } catch {
          localStorage.removeItem(STORAGE_KEY);
        }
      } else {
        // We have a token but no user info (e.g., after Google Login)
        // In a real app, you would call /auth/me here.
        // For now, let's create a placeholder user object from the token info if possible
        // or just set a generic user until /auth/me is implemented.
        const mockUser: User = {
          id: 'unknown',
          email: 'user@example.com',
          name: 'Authenticated User'
        };
        setUser(mockUser);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<{ error?: string }> => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        return { error: data.detail || 'Login failed' };
      }

      const { access_token } = await response.json();
      localStorage.setItem(TOKEN_KEY, access_token);

      // In a real app, you might fetch user profile here. 
      // For now, we'll store basic info.
      const loggedInUser: User = {
        id: btoa(email),
        email: email.toLowerCase(),
        name: email.split('@')[0], // Fallback name
      };

      setUser(loggedInUser);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedInUser));
      return {};
    } catch (err) {
      return { error: 'Connection error' };
    }
  };

  const signup = async (email: string, password: string, name: string): Promise<{ error?: string }> => {
    try {
      const response = await fetch(`${API_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: name }),
      });

      if (!response.ok) {
        const data = await response.json();
        return { error: data.detail || 'Signup failed' };
      }

      // Automatically log in after signup
      return login(email, password);
    } catch (err) {
      return { error: 'Connection error' };
    }
  };

  const loginWithGoogle = async (): Promise<{ error?: string }> => {
    window.location.href = `${API_URL}/auth/google/login`;
    return {};
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(TOKEN_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
