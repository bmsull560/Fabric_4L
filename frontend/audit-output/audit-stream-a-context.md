# Audit Stream A-Context — Context Engine (8 Pages)
**Date:** 2026-04-28  
**App:** Value Fabric Intelligence Platform

---

## Overview

The Context Engine provides 8 configuration/management pages.  
**Working: 4 | Broken: 4**

---

## Working Pages (4)

### /context/models — My Models
**Status:** ✅ Working

- Page renders correctly
- Skeleton loading state functional
- Empty state handled properly

---

### /context/value-trees/explorer — Tree Explorer
**Status:** ✅ Working

- Tree Explorer renders
- Empty state displays correctly

---

### /context/ingestion/jobs — Job Queue
**Status:** ✅ Working

- Job queue page renders
- Shows 0 jobs (empty state)
- All controls render correctly

---

### /context/extraction — Extraction Engine
**Status:** ✅ Working

- Extraction Engine page loads
- Configuration panel functional

---

## Broken Pages (4)

### /context/packs — Value Packs
**Status:** 🔴 Broken

**Error:**
```
expected array, received string
```

**Root Cause:** API returns wrong type (string instead of array)

---

### /context/formulas — Formulas
**Status:** 🔴 Broken

**Error:**
```
expected array, received string
```

**Root Cause:** Same API response type mismatch as Value Packs

---

### /context/agents — Agents
**Status:** 🔴 Broken

**Error:** Server 500

**Affected Areas:**
- Active Agents list
- Workflow History

---

### /context/ontology — Ontology
**Status:** 🔴 Broken

**Error:**
```
Failed to load ontology — Server 500
```

---

## Summary

| Page | Status | Error |
|------|--------|-------|
| /context/models | ✅ Working | — |
| /context/value-trees/explorer | ✅ Working | — |
| /context/ingestion/jobs | ✅ Working | — |
| /context/extraction | ✅ Working | — |
| /context/packs | 🔴 Broken | Type mismatch (string vs array) |
| /context/formulas | 🔴 Broken | Type mismatch (string vs array) |
| /context/agents | 🔴 Broken | Server 500 |
| /context/ontology | 🔴 Broken | Server 500 |
