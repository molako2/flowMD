import type { EngineInfo } from "../api/client";
import { fr } from "../i18n/fr";

export interface ConversionOptions {
  langs: string[];
  formats: string[];
  engine: string;
  forceOcr: boolean;
}

interface Props {
  options: ConversionOptions;
  engines: EngineInfo[];
  disabled: boolean;
  onChange: (options: ConversionOptions) => void;
}

const LANGS: { id: string; label: string }[] = [
  { id: "fr", label: fr.options.lang_fr },
  { id: "ar", label: fr.options.lang_ar },
  { id: "en", label: fr.options.lang_en },
];

const FORMATS: { id: string; label: string }[] = [
  { id: "md", label: fr.options.format_md },
  { id: "docx", label: fr.options.format_docx },
  { id: "xlsx", label: fr.options.format_xlsx },
];

function toggle(list: string[], value: string): string[] {
  return list.includes(value)
    ? list.filter((item) => item !== value)
    : [...list, value];
}

function CheckboxChip({
  checked,
  label,
  disabled,
  onToggle,
}: {
  checked: boolean;
  label: string;
  disabled: boolean;
  onToggle: () => void;
}) {
  return (
    <label
      className={`flex cursor-pointer select-none items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
        checked
          ? "border-indigo-500 bg-indigo-50 text-indigo-700"
          : "border-slate-300 bg-white text-slate-600 hover:border-slate-400"
      } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={onToggle}
        className="h-3.5 w-3.5 accent-indigo-600"
      />
      {label}
    </label>
  );
}

export default function OptionsPanel({
  options,
  engines,
  disabled,
  onChange,
}: Props) {
  return (
    <div className="space-y-4">
      <div>
        <p className="mb-2 text-sm font-semibold text-slate-700">
          {fr.options.languages}
        </p>
        <div className="flex flex-wrap gap-2">
          {LANGS.map((lang) => (
            <CheckboxChip
              key={lang.id}
              checked={options.langs.includes(lang.id)}
              label={lang.label}
              disabled={disabled}
              onToggle={() =>
                onChange({ ...options, langs: toggle(options.langs, lang.id) })
              }
            />
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 text-sm font-semibold text-slate-700">
          {fr.options.formats}
        </p>
        <div className="flex flex-wrap gap-2">
          {FORMATS.map((format) => (
            <CheckboxChip
              key={format.id}
              checked={options.formats.includes(format.id)}
              label={format.label}
              disabled={disabled}
              onToggle={() =>
                onChange({
                  ...options,
                  formats: toggle(options.formats, format.id),
                })
              }
            />
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label
            htmlFor="engine-select"
            className="mb-2 block text-sm font-semibold text-slate-700"
          >
            {fr.options.engine}
          </label>
          <select
            id="engine-select"
            value={options.engine}
            disabled={disabled}
            onChange={(e) => onChange({ ...options, engine: e.target.value })}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none"
          >
            {engines.map((engine) => (
              <option
                key={engine.id}
                value={engine.id}
                disabled={!engine.available}
              >
                {engine.label}
                {engine.available ? "" : ` (${fr.options.engineUnavailable})`}
              </option>
            ))}
          </select>
          {(() => {
            const selected = engines.find((e) => e.id === options.engine);
            return selected?.detail ? (
              <p className="mt-1 text-xs text-slate-500">{selected.detail}</p>
            ) : null;
          })()}
        </div>

        <div>
          <p className="mb-2 text-sm font-semibold text-slate-700">OCR</p>
          <label className="flex cursor-pointer items-start gap-2">
            <input
              type="checkbox"
              checked={options.forceOcr}
              disabled={disabled}
              onChange={(e) =>
                onChange({ ...options, forceOcr: e.target.checked })
              }
              className="mt-0.5 h-4 w-4 accent-indigo-600"
            />
            <span>
              <span className="block text-sm font-medium text-slate-700">
                {fr.options.forceOcr}
              </span>
              <span className="block text-xs text-slate-500">
                {fr.options.forceOcrHint}
              </span>
            </span>
          </label>
        </div>
      </div>
    </div>
  );
}
