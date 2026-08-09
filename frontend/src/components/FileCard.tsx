import type { FileOut } from "../api/client";
import { downloadUrl } from "../api/client";
import { fr } from "../i18n/fr";
import ProgressBar from "./ProgressBar";

interface Props {
  jobId: string;
  file: FileOut;
  onPreview: () => void;
}

const BADGE_STYLES: Record<FileOut["status"], string> = {
  pending: "bg-slate-100 text-slate-600",
  converting: "bg-indigo-50 text-indigo-700",
  exporting: "bg-indigo-50 text-indigo-700",
  done: "bg-emerald-50 text-emerald-700",
  error: "bg-red-50 text-red-700",
};

export default function FileCard({ jobId, file, onPreview }: Props) {
  const active = file.status === "converting" || file.status === "exporting";
  // Les avertissements du job sont déjà affichés au niveau du job : ne montrer
  // ici que ceux propres au fichier (déduplication par code).
  const fileWarnings = file.warnings;

  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <svg
            className="h-5 w-5 shrink-0 text-red-500"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M6 2a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6H6zm7 1.5L18.5 9H13V3.5zM8.5 13h1.2c.9 0 1.55.2 1.96.59.41.39.62.93.62 1.6 0 .68-.21 1.22-.63 1.61-.42.4-1.06.6-1.93.6h-.42V19H8.5v-6zm1.3 3.35c.44 0 .76-.1.97-.29.2-.19.31-.48.31-.86 0-.37-.1-.65-.3-.84-.2-.19-.5-.29-.92-.29h-.56v2.28h.5z" />
          </svg>
          <span
            className="truncate text-sm font-medium text-slate-800"
            title={file.name}
          >
            {file.name}
          </span>
          {file.page_count > 0 && (
            <span className="shrink-0 text-xs text-slate-400">
              {fr.jobs.pages(file.page_count)}
            </span>
          )}
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE_STYLES[file.status]}`}
        >
          {fr.jobs.status[file.status] ?? file.status}
        </span>
      </div>

      {active && <ProgressBar className="mt-2" />}

      {file.error && (
        <p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
          {file.error}
        </p>
      )}

      {fileWarnings.length > 0 && file.status === "done" && (
        <div className="mt-2 space-y-1">
          {fileWarnings.map((warning, index) => (
            <p
              key={`${warning.code}-${index}`}
              className="rounded-lg bg-amber-50 px-3 py-1.5 text-xs text-amber-800"
            >
              ⚠ {warning.message}
            </p>
          ))}
        </div>
      )}

      {file.status === "done" && file.outputs.length > 0 && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onPreview}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-indigo-400 hover:text-indigo-700"
          >
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
                d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {fr.jobs.preview}
          </button>
          {file.outputs.map((fmt) => (
            <a
              key={fmt}
              href={downloadUrl(jobId, file.id, fmt)}
              className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-2.5 py-1 text-xs font-semibold text-white transition-colors hover:bg-slate-950"
            >
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
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                />
              </svg>
              {fr.jobs.download[fmt] ?? fmt}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
