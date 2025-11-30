'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const tokens = await authApi.login(email, password);

      // Decode JWT to get user info (simple decode, not verify)
      const payload = JSON.parse(atob(tokens.access_token.split('.')[1]));

      login(tokens, {
        id: payload.sub,
        email: payload.email,
        role: payload.role,
        region: payload.region,
      });

      toast.success('Login successful');
      router.push('/dashboard');
    } catch (error: unknown) {
      toast.error('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = (role: string) => {
    switch (role) {
      case 'admin':
        setEmail('admin@nexusguard.io');
        setPassword('admin123');
        break;
      case 'engineer':
        setEmail('engineer@nexusguard.io');
        setPassword('engineer123');
        break;
      case 'viewer':
        setEmail('viewer@nexusguard.io');
        setPassword('viewer123');
        break;
    }
  };

  const handleAuth0Login = () => {
    // Redirect to Auth0 login endpoint
    window.location.href = '/api/auth/login';
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-100">
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="w-full max-w-md">
        <div className="rounded-lg bg-white p-8 shadow-lg">
          <div className="text-center mb-8">
            <img
              src="/nexusguard_noc.png"
              alt="NexusGuard NOC"
              width={80}
              height={80}
              className="mx-auto rounded-lg"
            />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">NexusGuard NOC</h1>
            <p className="mt-2 text-sm text-gray-500">
              Network Operations Center
            </p>
          </div>

          {/* Auth0 Login Button */}
          <button
            type="button"
            onClick={handleAuth0Login}
            className="w-full mb-6 rounded-md bg-black px-4 py-2 text-white font-medium hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0a12 12 0 1012 12A12 12 0 0012 0zm0 3.5a4.5 4.5 0 110 9 4.5 4.5 0 010-9z" />
            </svg>
            Sign in
          </button>
        </div>
        </div>
      </div>

      {/* Powered by Archpilot Footer */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Powered by</span>
          <span className="text-sm font-semibold text-white">Archpilot</span>
        </div>
        <span className="text-xs text-gray-500">&copy; {new Date().getFullYear()} Archpilot. All rights reserved.</span>
      </div>
    </div>
  );
}
