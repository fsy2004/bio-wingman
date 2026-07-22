# Data preparation workspace override

This page extends the Wingman Apple-style master for Bio Wingman's raw-data-to-analysis workflow.

## Information hierarchy

1. Show the downloaded/project-file choice before manual paste or table entry.
2. Keep every required primary and supporting input visible in one grouped section.
3. Label an input as one of: not prepared, selected file, software-generated, or connected upstream.
4. Disable Run until all project inputs exist; put the missing-input message next to the action.
5. Keep scientific parameters separate from file preparation.

## Workflow rules

- Never combine a user primary input with bundled supporting examples.
- Prefer upstream output reuse over asking the user to export, rename, or re-import a file.
- Use in-app editors for small semantic decisions such as case/control assignment; support multi-select and bulk actions.
- Do not auto-guess biological group meaning. Require an explicit user confirmation.
- Preserve all generated assets in the Bio Wingman run area and make them reproducible from the saved project.
- Use mature analysis/import modules for transformations; the UI coordinates them and does not reimplement statistics.

## Feedback

- File and upstream-asset readiness always includes text, not colour alone.
- Missing files disable Run and show an exact count.
- A failed transformation opens the log automatically; successful output becomes eligible for downstream auto-wiring.
