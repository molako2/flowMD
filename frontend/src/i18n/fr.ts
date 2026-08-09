/** Toute la copie française de l'interface, centralisée et typée. */

export const fr = {
  app: {
    title: "flowMD",
    tagline: "Convertissez vos PDF en Markdown, Word et Excel",
    localBadge: "100 % local — vos documents ne quittent jamais votre machine",
    footer:
      "flowMD — OCR et conversion de documents basés sur Docling (licence MIT). " +
      "Aucune donnée n'est envoyée sur Internet.",
  },
  banner: {
    modelsNotReady:
      "Premier démarrage : les modèles d'analyse (~2 Go) ne sont pas encore téléchargés. " +
      "Exécutez « flowmd setup » dans un terminal, sinon la première conversion " +
      "déclenchera le téléchargement et sera très lente.",
    doclingMissing:
      "Le moteur de conversion (docling) n'est pas installé dans cet environnement. " +
      "Exécutez « pip install -e . » puis redémarrez le serveur.",
  },
  dropzone: {
    title: "Glissez vos fichiers PDF ici",
    subtitle: "ou cliquez pour parcourir",
    onlyPdf: "Fichiers PDF uniquement",
    filesSelected: (n: number) =>
      n === 1 ? "1 fichier sélectionné" : `${n} fichiers sélectionnés`,
    clear: "Vider la liste",
  },
  options: {
    title: "Options de conversion",
    languages: "Langues du document",
    lang_fr: "Français",
    lang_ar: "العربية (arabe)",
    lang_en: "English (anglais)",
    formats: "Formats de sortie",
    format_md: "Markdown (.md)",
    format_docx: "Word (.docx)",
    format_xlsx: "Excel (.xlsx)",
    engine: "Moteur OCR",
    engineUnavailable: "indisponible",
    forceOcr: "Forcer l'OCR (document scanné)",
    forceOcrHint:
      "À activer si le PDF est un scan ou si sa couche texte est de mauvaise qualité.",
    convert: "Convertir",
    converting: "Conversion en cours…",
    needFiles: "Ajoutez au moins un fichier PDF.",
    needLangs: "Sélectionnez au moins une langue.",
    needFormats: "Sélectionnez au moins un format de sortie.",
  },
  jobs: {
    title: "Conversions",
    empty: "Aucune conversion pour l'instant. Déposez un PDF pour commencer.",
    downloadZip: "Tout télécharger (ZIP)",
    delete: "Supprimer",
    engine: "Moteur",
    pages: (n: number) => (n === 1 ? "1 page" : `${n} pages`),
    status: {
      pending: "En attente",
      converting: "Analyse et OCR en cours…",
      exporting: "Génération des fichiers…",
      done: "Terminé",
      error: "Erreur",
      processing: "En cours…",
    } as Record<string, string>,
    preview: "Aperçu",
    download: {
      md: "Markdown",
      docx: "Word",
      xlsx: "Excel",
    } as Record<string, string>,
  },
  preview: {
    title: "Aperçu Markdown",
    close: "Fermer",
    rtl: "Sens de lecture : droite à gauche",
    ltr: "Sens de lecture : gauche à droite",
    copy: "Copier le Markdown",
    copied: "Copié !",
    loading: "Chargement de l'aperçu…",
  },
  errors: {
    network: "Impossible de contacter le serveur flowMD. Est-il démarré ?",
    generic: "Une erreur est survenue.",
  },
};

export type FrDict = typeof fr;
