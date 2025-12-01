---
trigger: fileMatch
filePattern: "api/models.py"
description: Ensure database migrations are created after model changes
---

# Model Changes Hook

When modifying Django models, always:

## Required Steps
1. Make the model changes
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Update serializers if needed
5. Update API documentation

## Model Guidelines
- Use UUIDs for primary keys (for security)
- Add `created_at` and `updated_at` timestamps
- Index frequently queried fields
- Use `on_delete=CASCADE` carefully

## Checklist
- [ ] Migration created
- [ ] Migration applied
- [ ] Serializers updated
- [ ] Tests updated
