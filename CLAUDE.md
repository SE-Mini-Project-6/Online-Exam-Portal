# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Online Exam Portal** – a web-based examination system with two main user roles:

- **Admin** – creates and manages exams, questions, submissions, and results
- **Student** – attempts exams, answers questions, marks for review, submits, and views results

The project is divided into four deliverables, each owned by a team member:

| Deliverable | Description |
|---|---|
| **Deliverable 1** | Software Requirements Specification (SRS) |
| **Deliverable 2** | Test Plan |
| **Deliverable 3** | Software Architecture & Design Specification |
| **Deliverable 4** | Test Cases Update |

## Technology Stack

- **Backend**: Python / Django
- **API**: REST API
- **Database**: Relational Database
- **Version Control**: Git
- **Repository Hosting**: GitHub

## Repository Structure

```
Online-Exam-Portal/
├── README.md
├── Deliverable-1-SRS/
├── Deliverable-2-Test-Plan/
├── Deliverable-3-Architecture-Design/
└── Deliverable-4-Test-Cases/
```

## Common Development Commands

### Setup & Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate
```

### Running the Development Server

```bash
# Start the Django development server
python manage.py runserver
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run a specific test module
python manage.py test <module_name>

# Run tests with verbosity
python manage.py test -v 2
```

### Linting & Formatting

```bash
# Check code style with flake8
python -m flake8

# Format code with black
python -m black .

# Sort imports with isort
python -m isort .
```

### Code Quality

```bash
# Run mypy type checking (if configured)
python -m mypy .

# Generate coverage report
python -m pytest --cov=<app_name>
```

## Architecture & Structure

The project follows Django's MVT (Model-View-Template) pattern with a REST API layer. Key architectural elements:

- **Admin interface** for managing exams, questions, and viewing submissions
- **Student-facing portal** for attempting exams and viewing results
- **REST API** for client-server communication
- **Relational database** for persistent data storage
- **UML diagrams** documented in Deliverable 3 (Component Diagram, Sequence Diagrams, etc.)
- **Test coverage** documented in Deliverables 2 and 4 (7–10 test cases minimum)

## Deliverables Reference

- **Deliverable 1 (SRS)**: Project introduction, functional & non-functional requirements, UML Use Case Diagram, security objectives and requirements
- **Deliverable 2 (Test Plan)**: Test items, features to/test not tested, test approach, test environment, entry/exit criteria, security validation, traceability with SRS
- **Deliverable 3 (Architecture & Design)**: Component diagram, architectural pattern, requirement traceability, security architecture, deployment details, UML Sequence Diagrams, API design, error handling, data/state design
- **Deliverable 4 (Test Cases)**: Functional and non-functional test cases, preconditions, test steps, expected results, pass criteria, security validation, requirement traceability

## Git Workflow

The repository uses a feature-branch workflow:

```bash
# View recent commits and history
git log --oneline

# Check current status
git status

# Create and work on a feature branch
git checkout -b <branch-name>
```

Commit messages should follow the project conventions. End git commit messages with:
```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

Pull request descriptions should end with:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```