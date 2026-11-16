import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate } from "react-router-dom";
import type { z } from "zod";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";
import { useAuth } from "@/contexts/AuthContext";
import { errorMessage } from "@/services/http";
import { registerSchema } from "@/utils/validation";

type Values = z.infer<typeof registerSchema>;

export default function Register() {
  const { register: signUp } = useAuth();
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(registerSchema) });

  const onSubmit = handleSubmit(async (v) => {
    setFormError(null);
    try {
      await signUp(v.email, v.password, v.full_name);
      navigate("/app", { replace: true });
    } catch (e) {
      setFormError(errorMessage(e, "Could not create the account."));
    }
  });

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Analyze your resume against any job description."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {formError && (
          <p role="alert" className="rounded-md border border-danger/30 bg-danger/10 p-2 text-sm text-danger">
            {formError}
          </p>
        )}
        <Field label="Full name (optional)" error={errors.full_name?.message}>
          {(p) => <Input autoComplete="name" {...p} {...register("full_name")} />}
        </Field>
        <Field label="Email" error={errors.email?.message}>
          {(p) => <Input type="email" autoComplete="email" {...p} {...register("email")} />}
        </Field>
        <Field label="Password" error={errors.password?.message} hint="10+ characters with at least one letter and one number.">
          {(p) => <Input type="password" autoComplete="new-password" {...p} {...register("password")} />}
        </Field>
        <Field label="Confirm password" error={errors.confirm?.message}>
          {(p) => <Input type="password" autoComplete="new-password" {...p} {...register("confirm")} />}
        </Field>
        <Button type="submit" className="w-full" loading={isSubmitting}>
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}
