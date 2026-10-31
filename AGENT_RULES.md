# AGENT_RULES.md — FreightPilot AI Permanent Development Rules

These rules are permanent operational guardrails for all agents and contributors working on FreightPilot AI:

1. **Implement one milestone at a time.** Complete the current scope fully before advancing.
2. **Follow the existing documentation and avoid scope creep.** Adhere strictly to the specifications in `docs/`.
3. **Prefer short, readable, modular code over lengthy implementations.** Keep components and functions concise and single-purpose.
4. **Do not create unnecessary abstractions, files or dependencies.** Keep the architecture lightweight, lean, and direct.
5. **Do not duplicate existing functionality.** Reuse established services, utilities, schemas, and components.
6. **Validate inputs and handle errors explicitly.** Never assume external or client inputs are safe or well-formed.
7. **Use appropriate types and consistent naming.** Leverage TypeScript and Pydantic types across API and UI boundaries.
8. **Never expose secrets in frontend code or Git.** All credentials (`PAYPAL_CLIENT_SECRET`, `AI_API_KEY`) stay on the backend; never prefix secrets with `VITE_`.
9. **Never fake a successful PayPal transaction.** Never simulate checkout success with client mocks, static returns, or frontend redirect state; payment state must be verified and captured server-side against PayPal Sandbox.
10. **Use synthetic data only when it is clearly labelled.** Clearly mark demo shipments, carriers, quotes, and forecasts with `SANDBOX DEMO` / `SYNTHETIC_DEMO`.
11. **Add or update tests for every meaningful feature.** Unit, integration, and validation tests must accompany new logic.
12. **Run relevant tests and builds after each milestone.** Execute test suites and build steps to ensure zero regressions.
13. **Never claim a test passed unless you actually ran it.** Report actual execution output and commands run.
14. **Fix errors before proceeding to the next milestone.** Do not move forward with failing tests or broken builds.
15. **Do not rewrite working code unnecessarily.** Preserve working implementations and minimize churn.
16. **Do not silently ignore conflicting requirements.** Flag and document any contradictions or ambiguities explicitly.
