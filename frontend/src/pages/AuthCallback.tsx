import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const code = searchParams.get('code');

    if (code) {
      // Exchange code for real token via POST
      fetch(`http://localhost:8000/auth/google/token-exchange?code=${code}`, {
        method: 'POST',
      })
      .then(res => res.json())
      .then(data => {
        if (data.access_token) {
          const token = data.access_token;
          // Decode token or fetch user info. For now, we'll use a hack to get email.
          // In a real app, the exchange endpoint would return user info too.
          localStorage.setItem('rag_chat_token', token);
          
          // Redirect to home and let AuthContext handle the rest
          window.location.href = '/';
        } else {
          navigate('/auth');
        }
      })
      .catch(() => navigate('/auth'));
    } else {
      navigate('/auth');
    }
  }, [searchParams, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  );
}
