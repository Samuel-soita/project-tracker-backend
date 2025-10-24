import cloudinary
import cloudinary.uploader
from flask import current_app, has_app_context

def configure_cloudinary(app=None):
    """
    Configure Cloudinary using Flask app config.
    Can be called with an app or inside an app context.
    """
    config_source = app.config if app else (current_app.config if has_app_context() else None)
    
    if not config_source:
        raise RuntimeError("No Flask app context or app provided to configure Cloudinary.")

    cloudinary.config(
        cloud_name=config_source.get('CLOUDINARY_CLOUD_NAME'),
        api_key=config_source.get('CLOUDINARY_API_KEY'),
        api_secret=config_source.get('CLOUDINARY_API_SECRET')
    )

def upload_image(file, folder="project_covers"):
    """
    Upload an image to Cloudinary and return the secure URL.
    Accepts file path or file-like objects (e.g., Flask `FileStorage`).
    Returns None on failure.
    """
    try:
        # Ensure Cloudinary is configured
        if not cloudinary.config().cloud_name:
            configure_cloudinary()

        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            overwrite=True,
            resource_type="image"
        )
        return result.get('secure_url')
    except Exception as e:
        # Log the error (replace print with your logger if needed)
        print(f"[Cloudinary] Upload failed: {e}")
        return None