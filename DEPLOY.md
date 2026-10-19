# Share the guide with GitHub Pages

The complete website is already in [francismontalbo/khan_algo_CS](https://github.com/francismontalbo/khan_algo_CS). The repository owner can enable hosting without uploading or extracting any files.

1. Open the repository's [Settings → Pages](https://github.com/francismontalbo/khan_algo_CS/settings/pages).
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Select **main** and **/(root)**, then click **Save**.
4. Wait for deployment to finish, then click **Visit site** on the same settings page. Share that address with students.

Keep the supplied `.nojekyll` file at the repository root. GitHub's repository file viewer shows source files; **Visit site** opens the interactive guide. GitHub controls Pages availability through the account plan and repository policies.

GitHub's [publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) describe the same setup. These controls were checked on 19 October 2026.

## Update the published guide

Commit and push reviewed changes to `main`. GitHub Pages publishes that branch automatically. Follow [TESTING.md](TESTING.md) when editing the source assets or data. The supplied Checks workflow validates changes; Pages handles deployment.

## Optional local preview

Students can open a downloaded `index.html` directly. Maintainers who want an HTTP preview can run this command from the project folder if Python is installed.

```bash
python3 -m http.server 8000
```

Open [localhost:8000](http://localhost:8000/). Stop the preview with **Ctrl+C**.

## If something fails

- **404 at the homepage.** Check that Pages uses `main` and `/(root)`, with `index.html` at that root. Inspect the Pages deployment under **Actions**.
- **An old page appears.** Confirm the latest commit reached `main` and refresh the browser.
- **A video does not play.** Use its official-page fallback. External providers or school networks may block playback.
- **Notes appear missing.** Import an exported notes file. Local files and hosted pages use separate browser storage.
