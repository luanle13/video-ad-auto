# Contributing to AI Video Automation System

Thank you for your interest in contributing to the AI Video Automation System! We appreciate your time and effort in making this project better.

## Branch Strategy

We follow a GitFlow-inspired branching model:

### Branch Naming Convention

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/`: New feature development (e.g., `feature/user-authentication`)
- `bugfix/`: Bug fixes (e.g., `bugfix/login-error`)
- `hotfix/`: Critical production fixes (e.g., `hotfix/security-patch`)

### Creating a Branch

```bash
# From develop branch
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature/my-new-feature

# Or create a bugfix branch
git checkout -b bugfix/issue-fix
```

## Pull Request Process

1. **Fork the repository** (if you don't have direct write access)
2. **Create a feature branch** from `develop`
3. **Make your changes** following the coding standards
4. **Write or update tests** as needed
5. **Run all tests** to ensure nothing is broken
6. **Update documentation** as needed
7. **Commit your changes** with clear, descriptive messages
8. **Push to your fork** or origin
9. **Open a Pull Request** to the `develop` branch

### PR Title Format

Use the following format for PR titles:
```
[type]: Short description of changes

[feature]: Add user authentication
[bugfix]: Fix login error
[docs]: Update API documentation
[refactor]: Improve code structure
```

## Code Review Guidelines

### For Reviewers

- Check that the code follows the project's coding standards
- Ensure the code is well-documented
- Verify that tests are comprehensive and passing
- Consider performance implications
- Check for security vulnerabilities
- Ensure the changes align with the project's architecture

### For Contributors

- Address all review comments promptly
- If you disagree with a suggestion, provide a clear explanation
- Keep PRs focused on a single feature or bug fix
- Write clear, detailed descriptions for your PRs

## Development Guidelines

### Backend (Python)

- Follow PEP 8 style guide
- Use type hints everywhere
- Use Pydantic v2 models for data validation
- Use structured logging with structlog
- Write tests with pytest and aim for >80% coverage
- Use absolute imports from src root

### Frontend (React/TypeScript)

- Use TypeScript for all components
- Follow React best practices
- Use absolute imports from src root
- Write tests with Vitest and React Testing Library
- Use TailwindCSS for styling
- Follow accessibility best practices

### Infrastructure (Terraform)

- Use consistent naming conventions
- Document all resources
- Use modules for reusable components
- Keep state files secure

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/ai-video-platform.git
   ```

2. Set up the development environment (see README.md)

3. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. Push your changes and create a pull request

## Code of Conduct

Please follow our Code of Conduct in all interactions. Be respectful, inclusive, and constructive in all communications.

## Questions?

If you have any questions, feel free to open an issue or contact the maintainers.