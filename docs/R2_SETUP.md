# Cloudflare R2 Setup for Profile Image Uploads

This document explains how to configure Cloudflare R2 for storing user-uploaded profile images.

## What is R2?

Cloudflare R2 is an S3-compatible object storage service with zero egress fees. It's perfect for storing user-uploaded images, files, and other assets.

## Required Environment Variables

Add these to your `.env` file (backend):

```bash
# Cloudflare R2 Configuration
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
R2_BUCKET_NAME=blitz-uploads
R2_PUBLIC_URL=https://uploads.yourdomain.com  # Optional: Custom domain
```

## Setup Steps

### 1. Create Cloudflare R2 Bucket

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **R2** in the left sidebar
3. Click **Create bucket**
4. Name it `blitz-uploads` (or your preferred name)
5. Click **Create bucket**

### 2. Create API Token

1. In the R2 section, click **Manage R2 API Tokens**
2. Click **Create API token**
3. Give it a name like "Blitz Backend Upload"
4. Set permissions: **Object Read & Write**
5. Optionally limit to specific bucket
6. Click **Create API Token**
7. Copy the **Access Key ID** and **Secret Access Key** (you won't see the secret again!)

### 3. Get Your Account ID

1. In Cloudflare dashboard, look at the URL or sidebar
2. Your Account ID is visible in the R2 overview page
3. Copy it to your `.env` file

### 4. Configure Public Access (Optional)

**Option A: Public Bucket (Easiest)**
1. Go to your bucket settings
2. Enable **Public Access**
3. Your files will be accessible at: `https://blitz-uploads.YOUR_ACCOUNT_ID.r2.dev/`

**Option B: Custom Domain (Recommended for Production)**
1. Go to your bucket settings
2. Click **Connect Domain**
3. Enter your domain (e.g., `uploads.yourdomain.com`)
4. Follow DNS setup instructions
5. Set `R2_PUBLIC_URL=https://uploads.yourdomain.com` in your `.env`

### 5. Configure CORS (Important!)

To allow uploads from your frontend:

1. Go to your bucket settings
2. Click on **CORS policy**
3. Add this configuration:

```json
[
  {
    "AllowedOrigins": [
      "https://blitz.ws",
      "http://localhost:3000"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "POST",
      "DELETE"
    ],
    "AllowedHeaders": [
      "*"
    ],
    "ExposeHeaders": [
      "ETag"
    ],
    "MaxAgeSeconds": 3000
  }
]
```

## Testing the Setup

Once configured, test the upload functionality:

1. Deploy backend with new environment variables
2. Navigate to `/profile` page
3. Click "Edit Profile"
4. Click "Choose image file" and select an image
5. Click "Upload"
6. Image should upload to R2 and display in your profile

## File Structure in R2

Uploaded files are organized as follows:

```
blitz-uploads/
└── profile-images/
    ├── 20250116_123045_a1b2c3d4.jpg
    ├── 20250116_123156_e5f6g7h8.png
    └── ...
```

Filename format: `YYYYMMDD_HHMMSS_uniqueid.ext`

## Security Features

✅ **File Type Validation**: Only images (JPG, PNG, GIF, WebP) allowed
✅ **File Size Limit**: 5MB maximum
✅ **Unique Filenames**: Prevents overwrites and conflicts
✅ **Old Image Cleanup**: Deletes previous profile image on upload
✅ **S3-Compatible API**: Industry-standard security

## Cost

R2 is very affordable:
- **Storage**: $0.015/GB per month
- **Class A Operations** (uploads): $4.50 per million requests
- **Class B Operations** (downloads): Free!
- **Egress**: Free (this is the big benefit over S3!)

For a small to medium app with 10,000 users uploading 1 image each:
- Storage: ~50GB = $0.75/month
- Uploads: 10,000 requests = $0.045
- **Total: Less than $1/month**

## Troubleshooting

### "File upload service is not configured"
- Check that all R2 environment variables are set
- Restart your backend server after adding env vars

### "Access Denied" errors
- Verify your API token has read & write permissions
- Check bucket name matches your env variable
- Ensure token is for the correct Cloudflare account

### Images not displaying
- Check CORS configuration
- Verify public access is enabled (or custom domain is configured)
- Test the image URL directly in your browser

### "File type not allowed"
- Ensure image is JPG, PNG, GIF, or WebP
- Check file extension is correct

## Alternative: If You Don't Want to Use R2

If you don't want to set up R2, the profile page will still work but without image upload:
- Users will see default avatars (initials)
- The file upload button will show an error if clicked
- All other profile features work normally

To disable gracefully, just don't set the R2 environment variables.
