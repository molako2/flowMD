import { useCallback, useRef, useState } from "react";
import { fr } from "../i18n/fr";

interface Props {
  files: File[];
  onFiles: (files: File[]) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

export default function Dropzone({ files, onFiles }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return;
      const pdfs = Array.from(incoming).filter((f) =>
        f.name.toLowerCase().endsWith(".pdf"),
      );
      if (pdfs.length === 0) return;
      const known = new Set(files.map((f) => `${f.name}:${f.size}`));
      const fresh = pdfs.filter((f) => !known.has(`${f.name}:${f.size}`));
      onFiles([...files, ...fresh]);
    },
    [files, onFiles],
  );

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label={fr.dropzone.title}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragging
            ? "border-indigo-500 bg-indigo-50"
            : "border-slate-300 bg-white hover:border-indigo-400 hover:bg-indigo-50/40"
        }`}
      >
        <svg
          className={`h-10 w-10 ${dragging ? "text-indigo-500" : "text-slate-400"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 16.5V9m0 0l-3 3m3-3l3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"
          />
        </svg>
        <p className="text-base font-semibold text-slate-700">
          {fr.dropzone.title}
        </p>
        <p className="text-sm text-slate-500">{fr.dropzone.subtitle}</p>
        <p className="text-xs text-slate-400">{fr.dropzone.onlyPdf}</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          className="hidden"
          onChange={(e) => {
            addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {files.length > 0 && (
        <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">
              {fr.dropzone.filesSelected(files.length)}
            </span>
            <button
              type="button"
              onClick={() => onFiles([])}
              className="text-xs font-medium text-slate-500 hover:text-red-600"
            >
              {fr.dropzone.clear}
            </button>
          </div>
          <ul className="max-h-40 space-y-1 overflow-y-auto">
            {files.map((file, index) => (
              <li
                key={`${file.name}-${index}`}
                className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-1.5 text-sm"
              >
                <span className="truncate text-slate-700">{file.name}</span>
                <span className="flex shrink-0 items-center gap-2">
                  <span className="text-xs text-slate-400">
                    {formatSize(file.size)}
                  </span>
                  <button
                    type="button"
                    aria-label={`Retirer ${file.name}`}
                    onClick={() => onFiles(files.filter((_, i) => i !== index))}
                    className="rounded p-0.5 text-slate-400 hover:bg-slate-200 hover:text-red-600"
                  >
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
