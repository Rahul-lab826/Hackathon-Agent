import { z } from "zod";

export const registerSchema = z
  .object({
    full_name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain an uppercase letter")
      .regex(/[a-z]/, "Must contain a lowercase letter")
      .regex(/[0-9]/, "Must contain a number"),
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export const updateProfileSchema = z.object({
  full_name: z.string().min(2).max(255).optional(),
  username: z
    .string()
    .min(3)
    .max(30)
    .regex(/^[a-zA-Z0-9_]+$/, "Only letters, numbers, underscores")
    .optional(),
  bio: z.string().max(500).optional(),
  phone: z.string().max(20).optional(),
  location: z.string().max(255).optional(),
  website: z.string().url("Enter a valid URL").optional().or(z.literal("")),
});

export const hackathonBriefSchema = z.object({
  theme: z.string().min(3, "Theme is required").max(100),
  domain: z.string().min(2, "Domain is required"),
  duration_hours: z.number().min(12).max(72),
  audience_type: z.enum(["college_students", "professionals", "open", "mixed"]),
  expected_participants: z.number().min(10).max(10000),
  location_type: z.enum(["offline", "online", "hybrid"]),
  location_detail: z.string().optional(),
  special_requirements: z.string().max(1000).optional(),
});

export type RegisterFormData     = z.infer<typeof registerSchema>;
export type LoginFormData        = z.infer<typeof loginSchema>;
export type UpdateProfileData    = z.infer<typeof updateProfileSchema>;
export type HackathonBriefData   = z.infer<typeof hackathonBriefSchema>;
