---
name: find-docs
description: Fetch current library, framework, SDK, API, CLI, or cloud-service documentation with Context7 for syntax, configuration, setup, migration, and technology-specific debugging.
---

# Current documentation

Use the Context7 CLI for technology-specific documentation. General programming concepts,
business-logic debugging, refactoring, and code review do not require a lookup by themselves.
Use the execution environment's permitted network access; honor its approval policy.

1. Resolve the official product name with a focused documentation query:

   ```text
   npx ctx7@latest library "Next.js" "App Router middleware configuration"
   ```

2. Choose the exact official match using relevance, source reputation, snippet coverage, and score.
   Use the returned version-specific ID when the task requires that version. Resolve first unless
   the user supplies an ID in `/org/project` format.

3. Fetch the relevant concept, using the returned ID:

   ```text
   npx ctx7@latest docs /vercel/next.js "App Router middleware configuration"
   ```

Keep each query focused on one concept unless the question concerns their interaction. Use at most
three Context7 commands per question, including retries. Never include credentials or private code
in queries. Answer from the fetched documentation and cite its primary-source URLs. Check local
package versions when interpreting version-sensitive results.

For quota failures, explain the limit and suggest `npx ctx7@latest login` or the
`CONTEXT7_API_KEY` environment variable for higher limits, without printing its value. For network
or certificate failures, diagnose permitted connectivity and trusted certificate configuration;
retain TLS verification. If lookup remains unavailable, state the limitation and use accessible
official documentation when allowed. Clearly label any remaining uncertainty.
