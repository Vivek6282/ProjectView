import os
import mimetypes
from django.http import FileResponse, Http404

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'zip', 'rar', '7z'
}

SAFE_IMAGE_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp'
}


def validate_uploaded_file(uploaded_file):
    """
    Validate uploaded file size and extension.
    Returns (is_valid: bool, error_message: str).
    """
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, "File exceeds the 10 MB size limit."

    name = uploaded_file.name or ''
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if not ext or ext not in ALLOWED_EXTENSIONS:
        return False, f'File type ".{ext}" is not allowed.' if ext else 'Files without extensions are not allowed.'

    return True, ''


def build_safe_file_response(file_field_or_handle, filename=None, is_image=None):
    """
    Build a FileResponse with nosniff header, safe RFC-encoded Content-Disposition,
    inline display for safe images, and attachment download for other files.
    """
    if hasattr(file_field_or_handle, 'open'):
        try:
            file_handle = file_field_or_handle.open('rb')
        except (FileNotFoundError, ValueError, OSError):
            raise Http404("File not found on storage server.")
    else:
        file_handle = file_field_or_handle

    clean_filename = filename
    if not clean_filename and hasattr(file_field_or_handle, 'name'):
        clean_filename = os.path.basename(file_field_or_handle.name)
    if not clean_filename:
        clean_filename = 'download'

    ext = clean_filename.rsplit('.', 1)[-1].lower() if '.' in clean_filename else ''
    if is_image is None:
        is_image = ext in SAFE_IMAGE_EXTENSIONS

    content_type, _ = mimetypes.guess_type(clean_filename)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(
        file_handle,
        as_attachment=not is_image,
        filename=clean_filename,
        content_type=content_type,
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response
