# Reviewed publication queue

Put one article bundle per JSON file in this directory, then the scheduled workflow will publish at most one every 25 minutes once its review gate passes. Each bundle requires: `article` (full AR/EN/FR JSON), `sectionId`, `photo` (unique verified Unsplash photo), `resourceIds` (at least two existing official sources from `content/platform-links.json`) and `review` with `ready`, `checkedAt` (current UTC date), `sourcesIndependentlyChecked`, `translationsReviewed`, `photoProvenanceChecked` all set to true only after actual checks.

Queued articles are **not** site content until publication. The publisher refuses duplicate slugs/images, thin translations, or missing references. This workflow doesn't independently invent or write articles. It releases only genuinely completed reviewed submissions. GitHub schedules are not guaranteed to run at the exact minute.
