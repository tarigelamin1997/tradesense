# AI Service Fix

The AI service is failing due to a SQLAlchemy error where `metadata` is a reserved column name.

## Quick Fix:

In the AI service repository, change line 51 in `src/main.py`:

**From:**
```python
metadata = Column(JSON)
```

**To:**
```python
insight_metadata = Column(JSON)
```

Also update lines 282, 323, and 398 to use `insight_metadata` instead of `metadata`.

## To apply the fix:

1. Go to your AI service Railway project
2. Find the repository settings
3. Make these changes directly in the Railway editor or push to the connected repo
4. The service will automatically redeploy

The error is: `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.`