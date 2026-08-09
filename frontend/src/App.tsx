import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  createJob,
  deleteJob,
  getEngines,
  getJob,
  getPreview,
  type EnginesOut,
  type JobOut,
} from "./api/client";
import Dropzone from "./components/Dropzone";
import JobList from "./components/JobList";
import MarkdownPreview from "./components/MarkdownPreview";
import OptionsPanel, {
  type ConversionOptions,
} from "./components/OptionsPanel";
import { fr } from "./i18n/fr";

interface PreviewState {
  name: string;
  markdown: string | null;
}

interface Toast {
  id: number;
  message: string;
}

export default function App() {
  const [engines, setEngines] = useState<EnginesOut | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [options, setOptions] = useState<ConversionOptions>({
    langs: ["fr", "en"],
    formats: ["md", "docx", "xlsx"],
    engine: "auto",
    forceOcr: false,
  });
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [preview, setPreview] = useState<PreviewState | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastId = useRef(0);

  const notify = useCallback((message: string) => {
    const id = ++toastId.current;
    setToasts((current) => [...current, { id, message }]);
    setTimeout(
      () => setToasts((current) => current.filter((t) => t.id !== id)),
      6000,
    );
  }, []);

  useEffect(() => {
    getEngines()
      .then(setEngines)
      .catch(() => notify(fr.errors.network));
    // Rafraîchit l'état des moteurs quand l'utilisateur revient sur l'onglet
    // (ex. Tesseract installé entre-temps, serveur relancé).
    const refresh = () => {
      getEngines()
        .then(setEngines)
        .catch(() => {});
    };
    window.addEventListener("focus", refresh);
    return () => window.removeEventListener("focus", refresh);
  }, [notify]);

  // Rafraîchit les jobs actifs toutes les secondes.
  useEffect(() => {
    const active = jobs.filter(
      (job) => job.status === "pending" || job.status === "processing",
    );
    if (active.length === 0) return;
    const interval = setInterval(async () => {
      for (const job of active) {
        try {
          const updated = await getJob(job.id);
          setJobs((current) =>
            current.map((j) => (j.id === updated.id ? updated : j)),
          );
        } catch {
          /* le serveur redémarre peut-être : on réessaie au tick suivant */
        }
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [jobs]);

  const submit = async () => {
    if (files.length === 0) return notify(fr.options.needFiles);
    if (options.langs.length === 0) return notify(fr.options.needLangs);
    if (options.formats.length === 0) return notify(fr.options.needFormats);
    setSubmitting(true);
    try {
      const job = await createJob(files, options);
      setJobs((current) => [job, ...current]);
      setFiles([]);
    } catch (error) {
      notify(error instanceof ApiError ? error.message : fr.errors.network);
    } finally {
      setSubmitting(false);
    }
  };

  const removeJob = async (jobId: string) => {
    try {
      await deleteJob(jobId);
    } catch {
      /* déjà supprimé côté serveur */
    }
    setJobs((current) => current.filter((job) => job.id !== jobId));
  };

  const openPreview = async (jobId: string, fileId: string, name: string) => {
    setPreview({ name, markdown: null });
    try {
      const data = await getPreview(jobId, fileId);
      setPreview({ name, markdown: data.markdown });
    } catch (error) {
      setPreview(null);
      notify(error instanceof ApiError ? error.message : fr.errors.generic);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
              <svg
                className="h-6 w-6 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
                strokeLinecap="round"
              >
                <path d="M5 7h14M5 12h14M5 17h8" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">
                {fr.app.title}
              </h1>
              <p className="text-xs text-slate-500">{fr.app.tagline}</p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            <svg
              className="h-3.5 w-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
              />
            </svg>
            {fr.app.localBadge}
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-4 py-6">
        {engines && !engines.docling_installed && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {fr.banner.doclingMissing}
          </div>
        )}
        {engines && engines.docling_installed && !engines.models_ready && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {fr.banner.modelsNotReady}
          </div>
        )}

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <Dropzone files={files} onFiles={setFiles} />
          <div className="mt-5 border-t border-slate-100 pt-5">
            <OptionsPanel
              options={options}
              engines={engines?.engines ?? []}
              disabled={submitting}
              onChange={setOptions}
            />
          </div>
          <button
            type="button"
            onClick={submit}
            disabled={submitting || files.length === 0}
            className="mt-5 w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {submitting ? fr.options.converting : fr.options.convert}
          </button>
        </section>

        <section>
          <h2 className="mb-3 text-base font-semibold text-slate-800">
            {fr.jobs.title}
          </h2>
          <JobList jobs={jobs} onDelete={removeJob} onPreview={openPreview} />
        </section>
      </main>

      <footer className="mx-auto max-w-4xl px-4 pb-8">
        <p className="text-center text-xs text-slate-400">{fr.app.footer}</p>
      </footer>

      {preview && (
        <MarkdownPreview
          name={preview.name}
          markdown={preview.markdown}
          onClose={() => setPreview(null)}
        />
      )}

      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="max-w-sm rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-lg"
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}
