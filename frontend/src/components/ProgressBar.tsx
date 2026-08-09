/** Barre de progression indéterminée (Docling n'expose pas de pourcentage). */

interface Props {
  className?: string;
}

export default function ProgressBar({ className = "" }: Props) {
  return (
    <div
      role="progressbar"
      aria-label="Traitement en cours"
      className={`h-1.5 w-full overflow-hidden rounded-full bg-indigo-100 ${className}`}
    >
      <div className="h-full w-1/3 animate-[flowmd-slide_1.2s_ease-in-out_infinite] rounded-full bg-indigo-500" />
      <style>{`
        @keyframes flowmd-slide {
          0% { transform: translateX(-120%); }
          100% { transform: translateX(320%); }
        }
      `}</style>
    </div>
  );
}
