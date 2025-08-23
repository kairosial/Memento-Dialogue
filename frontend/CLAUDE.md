# CLAUDE.md — Frontend Development Guidelines

This document defines the rules and principles for all development work inside the `/frontend` directory.  
Claude Code must follow these instructions strictly when generating or modifying code.

---

## General Principles

-   **Production Quality Only**

    -   All code must be written at a level suitable for **real-world production use**.
    -   Do not generate placeholder, mock, or temporary implementations.
    -   Every feature should be robust, maintainable, and aligned with best practices for modern frontend engineering.

-   **Do Not Create New Servers**
    -   Never create or suggest launching a separate server on a new port number.
    -   The frontend must connect to the existing backend infrastructure (FastAPI + Supabase).
    -   Do not generate code that spins up additional Express, Node, or custom dev servers beyond the default React development server.

---

## React Development Guidelines

1. **Framework**

    - The frontend is built with **React** (functional components, hooks preferred).
    - Use **TypeScript (`.tsx`)** for new components whenever possible.

2. **Code Quality**

    - Follow clean code practices:
        - Keep components small and modular.
        - Use descriptive naming conventions.
        - Extract reusable logic into hooks or utility functions.
    - Include error handling and loading states for all async operations.

3. **State Management**

    - Prefer **React Query** (or equivalent) for server state synchronization with the backend.
    - Use React Context or lightweight state management libraries only when needed.
    - Avoid over-engineering with unnecessary global state.

4. **Styling**

    - Use **Tailwind CSS** for styling.
    - Components should follow a **consistent design system** (rounded corners, spacing, typography hierarchy).

5. **Integration with Backend**

    - All API calls must go through the existing backend (FastAPI or Supabase endpoints).
    - Do not hardcode alternative servers or ports.
    - Respect the separation of concerns:
        - Frontend = UI, UX, state management.
        - Backend = business logic, data processing.

6. **Testing**
    - Include **basic test coverage** (e.g., with Jest + React Testing Library).
    - Focus on testing critical UI flows and API interactions.

---

## Summary

-   **No placeholder code. No temporary hacks.**
-   **Do not spin up new servers or ports.**
-   **React code must be production-ready, maintainable, and integrated with the existing backend.**
