# API Contract

## Response Envelope

Every endpoint returns one of two shapes. The frontend can rely on
checking `success` to determine how to handle the response.

### Success

```json
{
  "success": true,
  "data": { ... }
}
```

HTTP status: `200` (GET, PUT, PATCH), `201` (POST create)

### Error

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Task with id 'abc-123' not found",
    "details": []
  }
}
```

## Error Codes

| Code | HTTP Status | When |
|---|---|---|
| `NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Unique constraint violation (duplicate name, etc.) |
| `VALIDATION_ERROR` | 422 | Input fails validation (Pydantic or business logic) |
| `INTERNAL_ERROR` | 500 | Unhandled server error |

### Validation Error Details

When `code` is `VALIDATION_ERROR`, the `details` array contains per-field errors:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {"field": "body -> title", "message": "Field required"},
      {"field": "body -> color", "message": "String should match pattern '^#[0-9a-fA-F]{6}$'"}
    ]
  }
}
```

## HTTP Methods

| Method | Semantics | Success Status |
|---|---|---|
| `GET` | Read resource(s) | `200 OK` |
| `POST` | Create resource | `201 Created` |
| `PUT` | Full update | `200 OK` |
| `PATCH` | Partial update | `200 OK` |
| `DELETE` | Soft-delete (archive) | `200 OK` |

## URL Conventions

- Base: `http://127.0.0.1:8787/api/v1`
- Resources are plural: `/tasks`, `/categories`, `/instances`
- Single resource: `/tasks/{id}`
- Sub-resources: `/instances/{id}/evidence`
- Actions: `/instances/generate` (POST)

## Pagination (future)

When pagination is needed, it will follow this shape:

```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 42,
    "page": 1,
    "page_size": 20
  }
}
```

Not implemented in Phase 1 (data volumes are small).

## Date/Time Formats

- Dates: `YYYY-MM-DD` (e.g., `"2026-06-22"`)
- Times: `HH:MM` (e.g., `"19:00"`)
- Timestamps: ISO 8601 with timezone (e.g., `"2026-06-22T06:41:20+00:00"`)

## File Uploads

Evidence file uploads use `multipart/form-data` with:
- Maximum file size: configurable (default 10 MB)
- Allowed alongside text fields in the same request
- Files are stored locally, never in the database
