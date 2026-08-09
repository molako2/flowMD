import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { fr } from "../i18n/fr";

interface Props {
  name: string;
  markdown: string | null;
  onClose: () => void;
}

/** Heuristique : le document est-il majoritairement en arabe ? */
function isMostlyArabic(text: string): boolean {
  const arabic = (text.match(/[؀-ۿ]/g) ?? []).length;
  const latin = (text.match(/[A-Za-z]/g) ?? []).length;
  return arabic > latin;
}

export default function MarkdownPreview({ name, markdown, onClose }: Props) {
  const [rtl, setRtl] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (markdown !== null) setRtl(isMostlyArabic(markdown));
  }, [markdown]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-label={fr.preview.title}
        className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-slate-800">
              {fr.preview.title}
            </h2>
            <p className="truncate text-xs text-slate-500">{name}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setRtl(!rtl)}
              className="rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-600 hover:border-indigo-400 hover:text-indigo-700"
              title={rtl ? fr.preview.rtl : fr.preview.ltr}
            >
              {rtl ? "RTL ←" : "LTR →"}
            </button>
            <button
              type="button"
              disabled={markdown === null}
              onClick={async () => {
                if (markdown === null) return;
                await navigator.clipboard.writeText(markdown);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
              className="rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-600 hover:border-indigo-400 hover:text-indigo-700"
            >
              {copied ? fr.preview.copied : fr.preview.copy}
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label={fr.preview.close}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            >
              <svg
                className="h-5 w-5"
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
          </div>
        </div>

        <div
          className="markdown-body overflow-y-auto px-6 py-4"
          dir={rtl ? "rtl" : "ltr"}
        >
          {markdown === null ? (
            <p className="py-8 text-center text-sm text-slate-400">
              {fr.preview.loading}
            </p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}
