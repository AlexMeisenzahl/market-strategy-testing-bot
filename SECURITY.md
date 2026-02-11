# Security Policy

## Supported Versions

We release security updates for the current major version. Upgrade to the latest release to receive security fixes.

## Reporting a Vulnerability

Please do **not** open public issues for security vulnerabilities.

- **Email**: Report suspected vulnerabilities privately to the maintainers (see repository contacts).
- **What to include**: Description of the issue, steps to reproduce, and impact.
- **Response**: We aim to acknowledge within 7 days and will work with you on a fix and disclosure.

## Security Practices

- **Secrets**: Never commit API keys, tokens, or passwords. Use `.env` (from `.env.example`) and keep it out of version control.
- **Configuration**: Use `config.yaml` for non-secret settings; keep secrets in environment variables or `.env`.
- **Dashboard**: Use a strong `SECRET_KEY` and `JWT_SECRET_KEY` in production; do not use default keys.
- **Paper trading**: This project is intended for paper trading only. Real-money trading requires additional security review.

## Dependency Security

- Dependencies are listed in `pyproject.toml` and `requirements.txt`.
- Run `pip install -e ".[dashboard,dev]"` from a clean environment to avoid supply-chain issues.
- Report any dependency vulnerabilities via the process above.
