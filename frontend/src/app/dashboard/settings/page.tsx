"use client";
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { User, Settings, Shield, Building2, Save, Key, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { updateProfileSchema, type UpdateProfileData } from "@/lib/validators";

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState("profile");
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<UpdateProfileData>({
    resolver: zodResolver(updateProfileSchema)
  });

  useEffect(() => {
    if (user) {
      reset({
        full_name: user.full_name || "",
        username: user.username || "",
        bio: user.bio || "",
        phone: user.phone || "",
        location: user.location || "",
        website: user.website || ""
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: UpdateProfileData) => {
    setIsLoading(true);
    try {
      const response = await api.patch("/users/me", data);
      setUser(response.data);
      toast.success("Profile updated successfully! ✨");
    } catch (err: any) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Failed to update profile.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="font-display font-bold text-3xl text-white">Settings</h1>
        <p className="text-surface-500 mt-1">Manage your account profile, organization, and security preferences</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Settings tabs sidebar */}
        <div className="w-full md:w-64 flex flex-row md:flex-col gap-2">
          {[
            { id: "profile", label: "Edit Profile", icon: User },
            { id: "org", label: "Organization", icon: Building2 },
            { id: "security", label: "Security & Plan", icon: Shield }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all border w-full text-left ${
                activeTab === tab.id
                  ? "bg-brand-500/10 border-brand-500 text-brand-300 shadow-glow-sm"
                  : "bg-transparent border-transparent text-surface-500 hover:text-surface-200"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content body */}
        <div className="flex-1">
          {activeTab === "profile" && (
            <form onSubmit={handleSubmit(onSubmit)} className="glass-card rounded-3xl p-8 space-y-6">
              <div className="flex items-center gap-2 pb-4 border-b border-white/5">
                <User className="w-5 h-5 text-brand-400" />
                <h3 className="text-lg font-bold text-white">Profile Details</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs text-surface-500 mb-1.5 font-bold uppercase tracking-wider">Full Name</label>
                  <input
                    {...register("full_name")}
                    className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                  {errors.full_name && <p className="text-red-400 text-xs mt-1">{errors.full_name.message}</p>}
                </div>

                <div>
                  <label className="block text-xs text-surface-500 mb-1.5 font-bold uppercase tracking-wider">Username</label>
                  <input
                    {...register("username")}
                    className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                  {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
                </div>

                <div>
                  <label className="block text-xs text-surface-500 mb-1.5 font-bold uppercase tracking-wider">Location</label>
                  <input
                    {...register("location")}
                    placeholder="e.g. San Francisco, CA"
                    className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs text-surface-500 mb-1.5 font-bold uppercase tracking-wider">Website</label>
                  <input
                    {...register("website")}
                    placeholder="https://example.com"
                    className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                  {errors.website && <p className="text-red-400 text-xs mt-1">{errors.website.message}</p>}
                </div>
              </div>

              <div>
                <label className="block text-xs text-surface-500 mb-1.5 font-bold uppercase tracking-wider">Bio / Description</label>
                <textarea
                  {...register("bio")}
                  rows={4}
                  className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="bg-gradient-brand text-white px-6 py-3 rounded-xl font-bold btn-lift shadow-glow-brand flex items-center gap-2 ml-auto disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Updating...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" /> Save Profile
                  </>
                )}
              </button>
            </form>
          )}

          {activeTab === "org" && (
            <div className="glass-card rounded-3xl p-8 space-y-6">
              <div className="flex items-center gap-2 pb-4 border-b border-white/5">
                <Building2 className="w-5 h-5 text-brand-400" />
                <h3 className="text-lg font-bold text-white">Organization Settings</h3>
              </div>

              <div className="space-y-4">
                <p className="text-sm text-surface-500">Currently, you are not affiliated with an organization. You can create a new organization below to begin collaborating with your team.</p>
                
                <div className="p-4 glass rounded-xl border border-white/5 space-y-3">
                  <p className="font-bold text-white text-sm">Multi-tenant Organizations</p>
                  <p className="text-xs text-surface-500 leading-relaxed">Upgrade to HackLaunch AI Team/Enterprise to support shared team workspaces, unified branding guides, custom templates, and advanced role assignments.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="glass-card rounded-3xl p-8 space-y-6">
              <div className="flex items-center gap-2 pb-4 border-b border-white/5">
                <Shield className="w-5 h-5 text-brand-400" />
                <h3 className="text-lg font-bold text-white">Security & Plan Info</h3>
              </div>

              <div className="space-y-6">
                <div className="p-5 glass rounded-2xl border border-white/5 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-white text-md">Your Current Plan</h4>
                    <p className="text-xs text-surface-500 mt-0.5">You are on the HackLaunch AI Free Trial tier.</p>
                  </div>
                  <span className="bg-brand-500/10 text-brand-300 border border-brand-500/20 px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wider">
                    {user?.plan || "Free"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
