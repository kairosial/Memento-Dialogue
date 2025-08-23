# CLAUDE.md — Backend Development Guidelines

This document defines **rules and principles** for working inside the `/backend` directory.  
Claude Code must carefully follow these instructions when generating or modifying code.

---

## General Principle

-   The backend uses **two layers**:
    1. **Supabase** → Handles simple, database-centric logic (CRUD, schema operations, queries).
    2. **FastAPI** → Handles complex logic requiring advanced processing, orchestration, or external integrations.

---

## Rules

1. **Simple Logic → Use Supabase**

    - If the task involves **basic CRUD** (Create, Read, Update, Delete) operations, simple queries, or straightforward database interactions, implement it in **Supabase**.
    - Do **NOT** create new FastAPI routes for tasks that Supabase can directly handle.

    **Examples of Supabase tasks**:

    - Insert, update, delete, or fetch rows.
    - Apply Row-Level Security (RLS) policies.
    - Run migrations for schema changes.
    - Manage simple user data retrieval.

---

2. **Complex Logic → Use FastAPI**

    - If the task requires **business logic, orchestration, or external services**, implement it in **FastAPI**.
    - Use FastAPI only when logic cannot be expressed easily with Supabase alone.

    **Examples of FastAPI tasks**:

    - Calling or integrating with **external APIs**.
    - Performing **complex data processing** or multi-step workflows.
    - Handling **custom authentication or authorization flows** beyond Supabase defaults.
    - Implementing **advanced business logic** that spans multiple systems.

---

3. **Separation of Concerns**
    - Do not duplicate logic between Supabase and FastAPI.
    - Always evaluate first:  
      **"Can this be done with Supabase alone?"** → If yes, then implement in Supabase.  
      If no, proceed with FastAPI.

---

## Summary

-   **Supabase = simple CRUD, schema, and direct DB logic.**
-   **FastAPI = complex logic, integrations, and workflows.**
-   Avoid mixing responsibilities: keep simple operations out of FastAPI.
