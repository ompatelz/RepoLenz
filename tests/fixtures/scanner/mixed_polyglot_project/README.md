# Mixed Polyglot Project

A sample multi-language repository fixture featuring a Python FastAPI backend and a TypeScript React frontend.

## Overview

This fixture is designed for testing repository scanners, multi-language detection, and polyglot dependency extraction in RepoLens.

## Project Structure

- `backend/`
  - `main.py`: FastAPI application exposing inventory REST endpoints (`/api/items`).
  - `models.py`: Pydantic data schemas representing item records and creation payloads.
- `frontend/`
  - `package.json`: Node.js / npm package configuration with React and TypeScript dependencies.
  - `src/App.tsx`: Root React component orchestrating the view layout.
  - `src/components/Header.tsx`: Presentational header navigation component.
  - `src/components/ItemList.tsx`: Item list component rendering catalog state.
  - `src/utils/format.ts`: Utility helpers for currency formatting and string manipulation.
