# Bundle Analysis

This document describes how to use the bundle analyzer to track and optimize the frontend bundle size.

## Local Usage

To analyze the bundle locally:

```bash
cd apps/web
pnpm run build:analyze
```

This will:
1. Build the application with bundle analysis enabled
2. Generate a visual report at `dist/public/stats.html`
3. Open the report in your browser (if configured)

Open `dist/public/stats.html` in your browser to view the interactive bundle visualization.

## CI Integration

Bundle analysis runs automatically in CI for every PR via `.github/workflows/pr-checks.yml`. The report is uploaded as an artifact named `bundle-report` with 14-day retention.

The bundle analysis step:
- Runs after the build step
- Does not fail the build (report-only)
- Uploads the HTML report as a CI artifact

## Suggested Thresholds (Future Enforcement)

After establishing a baseline, consider enforcing these thresholds:

| Metric | Warning Threshold | Critical Threshold |
|--------|------------------|-------------------|
| Initial JS entry chunk | 300-500 KB (gzip) | 700 KB (gzip) |
| Route chunk | 150-250 KB (gzip) | 400 KB (gzip) |
| Total initial payload | 700 KB-1 MB (gzip) | 1.5 MB (gzip) |

These are **guidelines only** until a baseline is established. To enforce thresholds in CI:

1. Add a step in `pr-checks.yml` after bundle analysis
2. Parse the bundle summary JSON
3. Compare against thresholds
4. Fail the build if exceeded

## Understanding the Report

The visualizer report shows:
- **Module size**: Individual file sizes
- **Gzipped size**: Compressed sizes (what users actually download)
- **Chunk composition**: Which modules belong to which chunks
- **Dependency tree**: How modules depend on each other

## Common Optimization Strategies

- **Code splitting**: Use dynamic imports for rarely used features
- **Tree shaking**: Ensure unused exports are removed
- **Lazy loading**: Load routes and components on demand
- **Externalize large libraries**: Use CDN for heavy dependencies
- **Compression**: Ensure gzip/brotli is enabled on the server

## Troubleshooting

If the bundle report is not generated:
- Ensure `rollup-plugin-visualizer` is installed
- Check that `ANALYZE=true` is set during build
- Verify the build completes successfully

## References

- [rollup-plugin-visualizer](https://github.com/btd/rollup-plugin-visualizer)
- [Vite Build Optimization](https://vitejs.dev/guide/build.html)
