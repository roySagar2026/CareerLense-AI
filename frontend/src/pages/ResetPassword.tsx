import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import type { z } from "zod";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";
import { useToast } from "@/contexts/ToastContext";
import { authApi } from "@/services/api";
import { errorMessage } from "@/services/http";
import { resetSchema } from "@/utils/validation";

type Values = z.infer<typeof resetSchema>;

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const navigate = useNavigate();
  const toast = useToast();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(resetSchema) });

  const onSubmit = handleSubmit(async ({ password }) => {
    setFormError(null);
    try {
      await authApi.resetPassword({ token, new_password: password });
      toast.success("Password updated. Please sign in.");
      navigate("/login", { replace: true });
    } catch (e) {
      setFormError(errorMessage(e));
    }
  });

  return (
    <AuthLayout
      title="Choose a new password"
      footer={
        <Link to="/login" className="text-accent hover:underline">
          Back to sign in
        </Link>
      }
    >
      {!token ? (
        <p role="alert" className="text-sm text-danger">
          This reset link is missing its token. Request a new link from the{" "}
          <Link to="/forgot-password" className="underline">
            forgot password
          </Link>{" "}
          page.
        </p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {formError && (
            <p role="alert" className="text-sm text-danger">
              {formError}
            </p>
          )}
          <Field label="New password" error={errors.password?.message}>
            {(p) => <Input type="password" autoComplete="new-password" {...p} {...register("password")} />}
          </Field>
          <Field label="Confirm password" error={errors.confirm?.message}>
            {(p) => <Input type="password" autoComplete="new-password" {...p} {...register("confirm")} />}
          </Field>
          <Button type="submit" className="w-full" loading={isSubmitting}>
            Update password
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
