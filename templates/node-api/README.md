# Node.js API starter

This dependency-free Node.js example uses the built-in test runner and demonstrates the reusable Node CI workflow. Replace `your-org` in `.github/workflows/ci.yml` with the toolkit repository owner and select a published release. The workflow requires a committed `package-lock.json` and runs `npm ci`, lint, tests, and build. `npm ci` executes dependency lifecycle scripts; review and pin dependencies in the consuming repository as part of normal supply-chain review.

Run `npm ci && npm run lint && npm test && npm run build` locally with Node.js 22 or newer.
