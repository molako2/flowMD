/** Client typé de l'API flowMD (même origine que l'interface). */

export interface ApiWarning {
  code: string;
  message: string;
}

export interface FileOut {
  id: string;
  name: string;
  status: "pending" | "converting" | "exporting" | "done" | "error";
  page_count: number;
  outputs: string[];
  warnings: ApiWarning[];
  error?: string | null;
}

export interface JobOut {
  id: string;
  status: "pending" | "processing" | "done" | "error";
  engine: string;
  langs: string[];
  formats: string[];
  force_ocr: boolean;
  files: FileOut[];
  warnings: ApiWarning[];
}

export interface EngineInfo {
  id: string;
  label: string;
  available: boolean;
  detail?: string;
  langs?: string[];
}

export interface EnginesOut {
  engines: EngineInfo[];
  models_ready: boolean;
  docling_installed: boolean;
}

export interface PreviewOut {
  file_id: string;
  name: string;
  markdown: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string = "UNKNOWN",
    public status: number = 0,
  ) {
    super(message);
  }
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erreur ${response.status}`;
    let code = "HTTP_ERROR";
    try {
      const body = await response.json();
      message = body.message ?? body.detail ?? message;
      code = body.code ?? code;
    } catch {
      /* corps non JSON */
    }
    throw new ApiError(message, code, response.status);
  }
  return response.json() as Promise<T>;
}

export async function getEngines(): Promise<EnginesOut> {
  return handle(await fetch("/api/engines"));
}

export interface CreateJobOptions {
  langs: string[];
  formats: string[];
  engine: string;
  forceOcr: boolean;
}

export async function createJob(
  files: File[],
  options: CreateJobOptions,
): Promise<JobOut> {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  form.append("langs", options.langs.join(","));
  form.append("formats", options.formats.join(","));
  form.append("engine", options.engine);
  form.append("force_ocr", String(options.forceOcr));
  return handle(await fetch("/api/jobs", { method: "POST", body: form }));
}

export async function getJob(jobId: string): Promise<JobOut> {
  return handle(await fetch(`/api/jobs/${jobId}`));
}

export async function deleteJob(jobId: string): Promise<void> {
  await handle(await fetch(`/api/jobs/${jobId}`, { method: "DELETE" }));
}

export async function getPreview(
  jobId: string,
  fileId: string,
): Promise<PreviewOut> {
  return handle(await fetch(`/api/jobs/${jobId}/files/${fileId}/preview`));
}

export function downloadUrl(jobId: string, fileId: string, fmt: string): string {
  return `/api/jobs/${jobId}/files/${fileId}/download/${fmt}`;
}

export function zipUrl(jobId: string): string {
  return `/api/jobs/${jobId}/download.zip`;
}
