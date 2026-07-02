"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Rocket, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { loginSchema, type LoginFormData } from "@/lib/validators";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const { data: tokens } = await api.post("/auth/login", data);
      const { data: user   } = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setAuth(tokens, user);
      toast.success(`Welcome back, ${user.full_name?.split(" ")[0] ?? "there"}! 👋`);
      router.push("/dashboard");
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 423) {
        toast.error("Account locked. Too many failed attempts. Try again later.");
      } else {
        toast.error("Invalid email or password.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      const { data } = await api.get("/auth/google");
      if (data?.auth_url) {
        window.location.href = data.auth_url;
      } else {
        toast.error("Failed to generate Google Login link.");
      }
    } catch (err) {
      toast.error("Failed to connect to Google authentication service.");
    }
  };

  return (
    <div className="min-h-screen bg-dark-500 flex items-center justify-center px-4 relative overflow-hidden">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-600/12 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-600/10 rounded-full blur-[80px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md relative z-10">

        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-3 mb-4 group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-brand flex items-center justify-center shadow-glow-brand group-hover:scale-110 transition-transform">
              <Rocket className="w-6 h-6 text-white" />
            </div>
            <span className="font-display font-bold text-2xl text-white">HackLaunch AI</span>
          </Link>
          <h1 className="font-display font-bold text-3xl text-white mt-2">Welcome back</h1>
          <p className="text-surface-500 mt-1">Sign in to your account</p>
        </div>

        {/* Google OAuth */}
        <button onClick={handleGoogleLogin}
          className="flex items-center justify-center gap-3 w-full bg-white/5 border border-white/10 rounded-xl p-3.5 text-surface-200 font-medium hover:border-white/20 hover:text-white hover:bg-white/10 transition-all mb-6 cursor-pointer">
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>

        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 h-px bg-white/8" />
          <span className="text-surface-600 text-sm">or</span>
          <div className="flex-1 h-px bg-white/8" />
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="glass-card rounded-2xl p-6 space-y-4">
          <div>
            <label className="block text-sm text-surface-300 mb-1.5 font-medium">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-600" />
              <input {...register("email")} type="email" placeholder="you@example.com"
                className="w-full bg-dark-300/60 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 pl-10 pr-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors" />
            </div>
            {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-sm text-surface-300 mb-1.5 font-medium">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-600" />
              <input {...register("password")} type={showPassword ? "text" : "password"} placeholder="Your password"
                className="w-full bg-dark-300/60 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 pl-10 pr-10 text-sm focus:border-brand-500/60 focus:outline-none transition-colors" />
              <button type="button" onClick={() => setShowPassword((p) => !p)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-600 hover:text-surface-300 transition-colors">
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
          </div>

          <button type="submit" disabled={isLoading}
            className="w-full bg-gradient-brand text-white py-3.5 rounded-xl font-bold text-sm btn-lift shadow-glow-sm disabled:opacity-60 disabled:cursor-not-allowed mt-2">
            {isLoading ? "Signing in…" : "Sign In →"}
          </button>
        </form>

        <p className="text-center text-sm text-surface-500 mt-5">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
            Sign up free
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
