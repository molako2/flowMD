import type { JobOut } from "../api/client";
import { zipUrl } from "../api/client";
import { fr } from "../i18n/fr";
import FileCard from "./FileCard";

interface Props {
  jobs: JobOut[];
  onDelete: (jobId: string) => void;
  onPreview: (jobId: string, fileId: string, name: string) => void;
}

export default function JobList({ jobs, onDelete, onPreview }: Props) {
  if (jobs.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-500">
        {fr.jobs.empty}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {jobs.map((job) => {
        const done = job.status === "done" || job.status === "error";
        const hasOutputs = job.files.some((f) => f.outputs.length > 0);
        return (
          <div
            key={job.id}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="rounded-full bg-slate-100 px-2 py-0.5 font-mono">
                  {job.id}
                </span>
                <span>
                  {fr.jobs.engine} : {job.engine} · {job.langs.join(", ")}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {done && hasOutputs && (
                  <a
                    href={zipUrl(job.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-700"
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
                    {fr.jobs.downloadZip}
                  </a>
                )}
                {done && (
                  <button
                    type="button"
                    onClick={() => onDelete(job.id)}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:border-red-300 hover:text-red-600"
                  >
                    {fr.jobs.delete}
                  </button>
                )}
              </div>
            </div>

            {job.warnings.length > 0 && (
              <div className="mb-3 space-y-1">
                {job.warnings.map((warning) => (
                  <p
                    key={warning.code}
                    className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800"
                  >
                    ⚠ {warning.message}
                  </p>
                ))}
              </div>
            )}

            <div className="space-y-2">
              {job.files.map((file) => (
                <FileCard
                  key={file.id}
                  jobId={job.id}
                  file={file}
                  onPreview={() => onPreview(job.id, file.id, file.name)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
