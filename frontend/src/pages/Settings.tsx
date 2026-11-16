import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import type { z } from "zod";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Field, Input, Select } from "@/components/ui/Field";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { useInvalidateAll } from "@/hooks/useQueries";
import { usersApi } from "@/services/api";
import { errorMessage, setAccessToken } from "@/services/http";
import { changePasswordSchema } from "@/utils/validation";

type PwValues = z.infer<typeof changePasswordSchema>;

function ProfileCard() {
  const { user, setUser } = useAuth();
  const toast = useToast();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [headline, setHeadline] = useState(user?.headline ?? "");
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try {
      setUser(await usersApi.update({ full_name: fullName.trim() || null, headline: headline.trim() || null }));
      toast.success("Profile saved.");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };
  return (
    <Card>
      <CardHeader title="Profile" description={user?.email} />
      <CardBody className="max-w-md space-y-4">
        <Field label="Full name">{(p) => <Input {...p} value={fullName} maxLength={120} onChange={(e) => setFullName(e.target.value)} />}</Field>
        <Field label="Headline" hint="For example: Backend engineer">{(p) => <Input {...p} value={headline} maxLength={160} onChange={(e) => setHeadline(e.target.value)} />}</Field>
        <Button loading={saving} onClick={save}>Save profile</Button>
      </CardBody>
    </Card>
  );
}

function PasswordCard() {
  const toast = useToast();
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<PwValues>({ resolver: zodResolver(changePasswordSchema) });
  const onSubmit = handleSubmit(async (v) => {
    try {
      await usersApi.changePassword({ current_password: v.current_password, new_password: v.new_password });
      reset();
      toast.success("Password changed.");
    } catch (e) {
      toast.error(errorMessage(e));
    }
  });
  return (
    <Card>
      <CardHeader title="Password" />
      <CardBody>
        <form onSubmit={onSubmit} className="max-w-md space-y-4" noValidate>
          <Field label="Current password" error={errors.current_password?.message}>{(p) => <Input type="password" autoComplete="current-password" {...p} {...register("current_password")} />}</Field>
          <Field label="New password" error={errors.new_password?.message}>{(p) => <Input type="password" autoComplete="new-password" {...p} {...register("new_password")} />}</Field>
          <Field label="Confirm new password" error={errors.confirm?.message}>{(p) => <Input type="password" autoComplete="new-password" {...p} {...register("confirm")} />}</Field>
          <Button type="submit" loading={isSubmitting}>Change password</Button>
        </form>
      </CardBody>
    </Card>
  );
}

function PrivacyCard() {
  const { user, setUser } = useAuth();
  const toast = useToast();
  const [saving, setSaving] = useState(false);
  const [retention, setRetention] = useState(String(user?.privacy_settings.retention_days ?? ""));
  const [store, setStore] = useState(user?.privacy_settings.store_original_files ?? true);
  useEffect(() => {
    if (user) {
      setRetention(String(user.privacy_settings.retention_days ?? ""));
      setStore(user.privacy_settings.store_original_files);
    }
  }, [user]);
  const save = async () => {
    setSaving(true);
    try {
      setUser(await usersApi.update({ privacy_settings: { retention_days: retention ? Number(retention) : null, store_original_files: store } }));
      toast.success("Privacy settings saved.");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };
  return (
    <Card>
      <CardHeader title="Privacy" description="Control how long your data is kept." />
      <CardBody className="max-w-md space-y-4">
        <label className="flex items-start gap-3 text-sm">
          <input type="checkbox" className="mt-1 h-4 w-4 accent-[#3978F6]" checked={store} onChange={(e) => setStore(e.target.checked)} />
          <span><span className="font-medium">Keep the original resume file</span><br /><span className="text-muted">Needed for previewing, downloading and reprocessing. If off, only extracted text is stored for new uploads.</span></span>
        </label>
        <Field label="Automatic deletion" hint="Retention is stored as your preference for automatic clean-up of old data.">
          {(p) => (
            <Select {...p} value={retention} onChange={(e) => setRetention(e.target.value)}>
              <option value="">Keep until I delete it</option><option value="30">After 30 days</option><option value="90">After 90 days</option><option value="365">After 1 year</option>
            </Select>
          )}
        </Field>
        <Button loading={saving} onClick={save}>Save privacy settings</Button>
      </CardBody>
    </Card>
  );
}

function DangerCard() {
  const { logout } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const invalidate = useInvalidateAll();
  const [dialog, setDialog] = useState<"data" | "account" | null>(null);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const close = () => { setDialog(null); setPassword(""); };
  const deleteData = async () => {
    setBusy(true);
    try {
      await usersApi.deleteData();
      await invalidate();
      toast.success("All resumes, job descriptions and analyses were deleted.");
      close();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  const deleteAccount = async () => {
    setBusy(true);
    try {
      await usersApi.deleteAccount(password);
      setAccessToken(null);
      await logout().catch(() => undefined);
      toast.success("Your account was deleted.");
      navigate("/", { replace: true });
    } catch (e) {
      toast.error(errorMessage(e));
      setBusy(false);
    }
  };

  return (
    <Card className="border-danger/40">
      <CardHeader title="Danger zone" description="These actions can't be undone." />
      <CardBody className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="text-sm font-medium">Delete all my data</p><p className="text-xs text-muted">Removes every resume, job description and analysis. Your account stays.</p></div>
          <Button variant="danger" onClick={() => setDialog("data")}>Delete all data</Button>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
          <div><p className="text-sm font-medium">Delete my account</p><p className="text-xs text-muted">Permanently removes your account and everything in it.</p></div>
          <Button variant="danger" onClick={() => setDialog("account")}>Delete account</Button>
        </div>
      </CardBody>
      <ConfirmDialog open={dialog === "data"} onOpenChange={(o) => !o && close()} title="Delete all your data?" description="Every resume, job description and analysis will be permanently deleted." confirmLabel="Delete everything" loading={busy} onConfirm={deleteData} />
      <ConfirmDialog open={dialog === "account"} onOpenChange={(o) => !o && close()} title="Delete your account?" description="Your account and all of its data will be permanently deleted. Enter your password to confirm." confirmLabel="Delete account" loading={busy} onConfirm={() => password && deleteAccount()}>
        <Field label="Password">{(p) => <Input type="password" autoComplete="current-password" {...p} value={password} onChange={(e) => setPassword(e.target.value)} />}</Field>
      </ConfirmDialog>
    </Card>
  );
}

export default function Settings() {
  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader title="Settings" description="Manage your account, privacy and data." />
      <ProfileCard />
      <PasswordCard />
      <PrivacyCard />
      <DangerCard />
    </div>
  );
}
