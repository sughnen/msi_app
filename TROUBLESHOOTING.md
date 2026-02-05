# MSI Training Portal - Setup & Troubleshooting Guide

## Why You're Seeing a Blank Page

The blank page issue is caused by several problems in your original code:

1. **Corrupted Logo Image** - The base64 image data is invalid/incomplete
2. **Missing Supabase Configuration** - No secrets.toml file configured
3. **CSS Auth Wrapper** - The CSS was hiding content improperly
4. **Missing Error Handling** - Errors were not being displayed

## Quick Fix Steps

### 1. Install Required Packages

```bash
pip install streamlit pandas supabase pillow
```

### 2. Configure Supabase Credentials

Create the directory structure:
```bash
mkdir -p .streamlit
```

Copy the template and edit with your credentials:
```bash
cp secrets.toml.template .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-public-key-here"
```

### 3. Run the Fixed App

```bash
streamlit run msi_training_portal_fixed.py
```

## What Was Fixed

### 1. Logo Function
- **Before**: Corrupted base64 data caused PIL errors
- **After**: Creates a simple colored placeholder or text fallback

### 2. Supabase Connection
- **Before**: Silent failure if credentials missing
- **After**: Clear error messages with setup instructions

### 3. Authentication UI
- **Before**: CSS wrapper caused display issues
- **After**: Simple column-based layout that always renders

### 4. Error Handling
- **Before**: Exceptions caused blank screens
- **After**: Try-catch blocks with user-friendly error messages

### 5. Demo Mode
- **Before**: App wouldn't work without database
- **After**: Falls back to demo mode for testing

## Testing Without Supabase

The fixed app includes a **demo mode** that lets you test the UI without configuring Supabase:

1. Just run the app without creating secrets.toml
2. You'll see a warning but can still test login/forms
3. Use any email/password to login in demo mode
4. Use email `admin@msi.org` to access admin features

## Supabase Database Setup

If you haven't set up your Supabase tables yet, run these SQL commands in your Supabase SQL Editor:

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    reset_code TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enrollments table
CREATE TABLE enrollments (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    surname TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    training_type TEXT NOT NULL,
    training_date DATE NOT NULL,
    pretest_file TEXT NOT NULL,
    posttest_file TEXT NOT NULL,
    supporting_documents TEXT[] NOT NULL,
    status TEXT DEFAULT 'Submitted',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create storage bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('enrollments', 'enrollments', false);

-- Storage policies (adjust as needed)
CREATE POLICY "Allow authenticated users to upload" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (bucket_id = 'enrollments');

CREATE POLICY "Allow authenticated users to download" 
ON storage.objects FOR SELECT 
TO authenticated 
USING (bucket_id = 'enrollments');
```

## Common Issues & Solutions

### Issue: "Module 'supabase' not found"
**Solution:** Install the package
```bash
pip install supabase
```

### Issue: "Module 'PIL' not found"
**Solution:** Install Pillow
```bash
pip install pillow
```

### Issue: Still seeing blank page
**Solution:** Check terminal/console for errors
- Run with verbose output: `streamlit run msi_training_portal_fixed.py --logger.level=debug`
- Look for error messages in the terminal

### Issue: "Supabase credentials not configured"
**Solution:** 
1. Verify `.streamlit/secrets.toml` exists
2. Check file permissions (should be readable)
3. Verify credentials are correct from Supabase dashboard

### Issue: Can't login with demo mode
**Solution:** 
- Enter ANY email and password (it will accept anything in demo mode)
- For admin access in demo mode, use email: `admin@msi.org`

## File Structure

Your project should look like this:

```
your-project/
├── msi_training_portal_fixed.py    # Main app file
├── .streamlit/
│   └── secrets.toml                # Supabase credentials (create this)
└── requirements.txt                # Python dependencies
```

## requirements.txt

Create this file with:
```
streamlit>=1.28.0
pandas>=2.0.0
supabase>=2.0.0
pillow>=10.0.0
```

## Next Steps

1. Test the app in demo mode first
2. Set up your Supabase project and tables
3. Configure secrets.toml with real credentials
4. Test database connectivity
5. Create your first admin user
6. Deploy to production

## Getting Help

If you still have issues:
1. Check the terminal output for specific error messages
2. Verify all packages are installed: `pip list | grep -E "streamlit|supabase|pillow|pandas"`
3. Test Supabase connection separately
4. Enable debug logging

## Security Notes

⚠️ **Important Security Reminders:**
- Never commit `.streamlit/secrets.toml` to git (add to .gitignore)
- Use Row Level Security (RLS) policies in Supabase
- Store passwords hashed (already implemented)
- Use environment variables in production
- Enable HTTPS for production deployment
