<wizard-report>
# PostHog post-wizard report

The wizard has completed a deep integration of PostHog analytics into the AI Learning System FastAPI backend. A dedicated `app/core/posthog.py` module was created to hold the singleton `Posthog` client, avoiding circular import issues. The client is initialized with `enable_exception_autocapture=True` for automatic error tracking, is disabled when `POSTHOG_API_KEY` is not set (safe for local dev without credentials), and is flushed on both app shutdown (lifespan) and process exit (`atexit`). PostHog settings (`POSTHOG_API_KEY`, `POSTHOG_HOST`) were added to Pydantic Settings in `app/core/config.py` and written to the `.env` file. User identification (`identify_context`) is called on registration and login so backend events are correlated with users.

## Events instrumented

| Event name | Description | File |
|---|---|---|
| `user registered` | New user successfully creates an account; person properties set on signup | `app/api/endpoints/auth.py` |
| `user logged in` | User authenticates via form or JSON endpoint; user identified in context | `app/api/endpoints/auth.py` |
| `user logged out` | User ends their session | `app/api/endpoints/auth.py` |
| `password reset requested` | User requests a password reset email | `app/api/endpoints/auth.py` |
| `file uploaded` | User uploads a document or image; includes `file_type`, `file_size_kb`, `mime_type` | `app/api/endpoints/files.py` |
| `file deleted` | User soft-deletes a file from their library | `app/api/endpoints/files.py` |
| `quiz created` | User triggers AI quiz generation; includes `num_questions`, `ai_provider`, `shuffle_questions` | `app/api/endpoints/quizzes.py` |
| `quiz attempt started` | User begins a new quiz attempt | `app/api/endpoints/quizzes.py` |
| `quiz attempt completed` | User submits answers; includes `score`, `total_points`, `percentage`, `passed` | `app/api/endpoints/quizzes.py` |
| `knowledge queried` | User submits a RAG query; includes `chunks_used`, `query_length`, `top_k` | `app/api/endpoints/knowledge.py` |
| `study plan item completed` | User marks a scheduled study item as done; includes `priority`, `has_attempt` | `app/api/endpoints/study_plan.py` |

## Files changed

- `app/core/posthog.py` — **new**: singleton PostHog client module
- `app/core/config.py` — added `POSTHOG_API_KEY` and `POSTHOG_HOST` settings
- `app/main.py` — imports PostHog client; calls `posthog_client.flush()` on shutdown
- `app/api/endpoints/auth.py` — `user registered`, `user logged in` (×2), `user logged out`, `password reset requested`
- `app/api/endpoints/files.py` — `file uploaded`, `file deleted`
- `app/api/endpoints/quizzes.py` — `quiz created`, `quiz attempt started`, `quiz attempt completed`
- `app/api/endpoints/knowledge.py` — `knowledge queried`
- `app/api/endpoints/study_plan.py` — `study plan item completed`
- `requirements.txt` — added `posthog>=3.0.0`
- `.env` — added `POSTHOG_API_KEY` and `POSTHOG_HOST`

## Next steps

We've built a dashboard and 5 insights to monitor user behavior as soon as events start flowing:

- **Dashboard — Analytics basics**: https://eu.posthog.com/project/157846/dashboard/616904
- **User Acquisition Funnel** (registration → file upload → quiz created → quiz completed): https://eu.posthog.com/project/157846/insights/K7UGz9Vj
- **Daily Active Users (Logins)**: https://eu.posthog.com/project/157846/insights/ysskHcUY
- **Quiz Pass vs Fail Rate**: https://eu.posthog.com/project/157846/insights/82c6tCnx
- **File Uploads by Type**: https://eu.posthog.com/project/157846/insights/jDAVBMZX
- **Core Feature Engagement** (knowledge queries, study plan completions, registrations): https://eu.posthog.com/project/157846/insights/1qMKXw51

### Agent skill

We've left an agent skill folder in your project at `.claude/skills/integration-fastapi/`. You can use this context for further agent development when using Claude Code. This will help ensure the model provides the most up-to-date approaches for integrating PostHog.

</wizard-report>
