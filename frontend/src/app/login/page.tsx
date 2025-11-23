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

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-primary-600 px-4 py-2 text-white font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6">
            <p className="text-center text-xs text-gray-500 mb-3">Demo Accounts</p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => fillDemoCredentials('admin')}
                className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('engineer')}
                className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50"
              >
                Engineer
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('viewer')}
                className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50"
              >
                Viewer
              </button>
            </div>
          </div>
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
