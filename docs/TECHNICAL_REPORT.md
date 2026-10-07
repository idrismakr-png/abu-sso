# Technical Report
## ABU-SSO: Unified Single Sign-On & Digital Campus Wallet

**Course:** COEN838 — Advanced Software Engineering  
**Department:** Computer Engineering, Ahmadu Bello University, Zaria  
**Student:** Idris Muhammad Abubakar  
**Matric No:** P25EGCP9003  
**Date:** October 2026  

**Repository:** https://github.com/idrismakr-png/abu-sso

---

## Abstract

Nigerian university students routinely juggle multiple credentials across isolated systems (student portal, LMS, Wi-Fi, library, hostel), leading to password fatigue, forgotten logins, and shared accounts. This report documents the engineering of **ABU-SSO** — a unified single sign-on and digital campus wallet for Ahmadu Bello University — following the Software Engineering process taught in COEN838 (Modules I–V). The system is built with Python 3.12, FastAPI, SQLAlchemy, and JWT-based authentication. It was delivered in ten iterative increments, is covered by 53 automated tests achieving 96% line coverage, runs a green CI pipeline on every push, and has passed a Bandit SAST scan with zero findings. The report closes with a risk register, maintenance plan, and reflections on lessons learned.

---

## 1. Introduction

### 1.1 Problem Statement

Students at Ahmadu Bello University interact with at least five separate digital systems, each with its own credentials:

1. Central student portal (course registration, results)
2. Learning Management System (Moodle)
3. Campus Wi-Fi captive portal
4. Library borrowing system
5. Hostel allocation and gate access

Passwords are frequently forgotten, reused across systems, or shared with peers — a security and productivity problem. Identity is duplicated across the systems, violating the "once-only" registration principle.

### 1.2 Goal

Design and build a **single identity provider** for ABU campus services, with a **digital wallet** for payments, exposed via a **documented REST API** so any campus service can trust one login.

### 1.3 Scope

- Central authentication (register, login, JWT issuance).
- Digital ID card with QR code.
- Campus wallet (top-up, payment, transaction history).
- Web dashboard.
- Auto-generated OpenAPI documentation.
- Automated tests + continuous integration.

Out of scope: real payment gateways, native mobile apps, biometric authentication, and integration with the real ABU ERP.

---

## 2. Engineering Process

### 2.1 Methodology — Agile, Iterative

An **iterative and incremental Agile** process was used because the problem statement involves real users with evolving needs. Each increment produced a working, demonstrable slice of the system:

| Increment | Deliverable |
|-----------|-------------|
| 1 | Project scaffold + Git + GitHub repo |
| 2 | FastAPI base + health endpoint |
| 3 | Modular architecture (config, routers) |
| 4 | SQLAlchemy + User model |
| 5 | bcrypt password hashing + user service |
| 6 | JWT auth endpoints |
| 7 | Digital ID card + QR |
| 8 | Campus wallet |
| 9 | Web UI (login + dashboard) |
| 10 | 53 automated tests + GitHub Actions CI |

**Why not Waterfall?** Wallet integration was added *after* the auth prototype was working — an upfront plan could not have anticipated the exact wallet schema. Iteration allowed course correction.

### 2.2 Requirements Engineering (Module I)

Requirements were elicited using three techniques:

- **Interviews** with 3 ABU students.
- **Ethnography** — observing students in the Faculty of Engineering computer lab.
- **Document analysis** — the ABU ICT Directorate's policy on the "once-only" principle.

15 Functional Requirements (FR-01 to FR-15) and 12 Non-Functional Requirements (NFR-01 to NFR-12) are documented in `docs/SRS.md`. Requirements are modelled with:

- Use Case diagram (10 use cases)
- Sequence diagram (login + protected resource)
- Class diagram (User, Wallet, Transaction)

A **Requirements Traceability Matrix** (`docs/RTM.md`) links every FR to its design artefact, source file, and automated test.

### 2.3 Architecture & Design (Module III)

**Architectural style:** Modular monolith with a layered architecture, organised around **feature routers** rather than technical layers. This choice balances two constraints:

- **Student-solo build** — a microservices deployment would be overkill for one developer.
- **Growth path to microservices** — each router (`auth`, `wallet`, `id_card`) is already isolated behind a clear service boundary, so it can be extracted into its own service later.

**Layers:**
