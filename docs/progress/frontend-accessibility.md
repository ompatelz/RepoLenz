# Frontend Accessibility and Testing Coverage

## Overview

RepoLens is built to provide an intuitive, accessible experience for all developers.
Feature 5 introduces enhanced keyboard shortcuts, ARIA navigation roles, screen reader
live announcements, and expanded Vitest test coverage.

## Key Improvements

1. **Global Keyboard Navigation**:
   - Pressing `/` or `Ctrl+K` / `Cmd+K` from anywhere outside form inputs automatically
     focuses the node search input.
   - Pressing `Escape` hierarchically dismisses active states: clearing selected node focus,
     exiting drill-down scope, or clearing search text.

2. **Semantic ARIA Roles and Hierarchy Tracking**:
   - Breadcrumbs navigation provides `aria-current="page"` for the active drill-down component.
   - Level switcher tabs are implemented as an accessible tablist (`role="tablist"`, `role="tab"`,
     `aria-selected`, `aria-controls="map"`).
   - High-contrast `:focus-visible` styling ensures clear visual indicators during keyboard navigation.

3. **Screen Reader Live Announcements**:
   - An `aria-live="polite"` region provides concise auditory context updates whenever the user
     drills into a component, focuses a neighborhood, or changes active filters.

4. **Expanded Frontend Test Suite**:
   - Added `frontend/src/a11y.test.ts` testing label formatting, breadcrumb page tracking,
     and announcement formatting.
   - Vitest suite expanded to 15 passing tests.
