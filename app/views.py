from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app
)
from app.models import (
    get_all_articles, get_article, insert_article,
    update_article, delete_article, get_user
)
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename
import msal
import os
import uuid
import logging

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated


def _build_msal_app():
    return msal.ConfidentialClientApplication(
        current_app.config['CLIENT_ID'],
        authority=current_app.config['AUTHORITY'],
        client_credential=current_app.config['CLIENT_SECRET'],
    )


# ── Blob helper ───────────────────────────────────────────────────────────────

def upload_image(image_file):
    """Upload image to local static storage or Azure Blob Storage and return a URL."""
    if current_app.config['IMAGE_UPLOAD_BACKEND'] == 'local':
        return upload_local_image(image_file)

    return upload_blob_image(image_file)


def upload_local_image(image_file):
    filename = secure_filename(image_file.filename)
    if not filename:
        return ''

    filename = f"{uuid.uuid4().hex}_{filename}"
    upload_folder = current_app.config['LOCAL_UPLOAD_FOLDER']
    upload_path = os.path.join(current_app.static_folder, upload_folder)
    os.makedirs(upload_path, exist_ok=True)

    image_file.save(os.path.join(upload_path, filename))
    return url_for('static', filename=f"{upload_folder}/{filename}")


def upload_blob_image(image_file):
    """Upload image to Azure Blob Storage and return public URL."""
    blob_service = BlobServiceClient.from_connection_string(
        current_app.config['BLOB_CONNECTION_STRING']
    )
    container_client = blob_service.get_container_client(
        current_app.config['BLOB_CONTAINER']
    )
    blob_name = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(image_file, overwrite=True)
    return blob_client.url


def delete_image(image_url):
    """Delete a local image or blob by URL (best-effort)."""
    static_prefix = url_for('static', filename='', _external=False)
    if image_url.startswith(static_prefix):
        delete_local_image(image_url)
    else:
        delete_blob(image_url)


def delete_local_image(image_url):
    try:
        static_prefix = url_for('static', filename='', _external=False)
        relative_path = image_url.split(static_prefix, 1)[-1]
        upload_folder = current_app.config['LOCAL_UPLOAD_FOLDER']
        if not relative_path.startswith(f"{upload_folder}/"):
            return

        file_path = os.path.abspath(os.path.join(current_app.static_folder, relative_path))
        static_folder = os.path.abspath(current_app.static_folder)
        if os.path.commonpath([static_folder, file_path]) == static_folder and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Could not delete local image: {e}")


def delete_blob(image_url):
    """Delete a blob by URL (best-effort)."""
    try:
        blob_service = BlobServiceClient.from_connection_string(
            current_app.config['BLOB_CONNECTION_STRING']
        )
        container = current_app.config['BLOB_CONTAINER']
        blob_name = image_url.split(f"/{container}/")[-1]
        blob_service.get_blob_client(container=container, blob=blob_name).delete_blob()
    except Exception as e:
        logger.warning(f"Could not delete blob: {e}")


# ── Routes ────────────────────────────────────────────────────────────────────

@main.route('/')
@login_required
def index():
    articles = get_all_articles()
    user = session.get('user', {})
    return render_template('index.html', articles=articles, user=user)


# ── Login / Logout ────────────────────────────────────────────────────────────

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = get_user(username, password)
        if user:
            session['user'] = {'id': user[0], 'username': user[1], 'type': 'local'}
            logger.info(f"Successful login: {username}")
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('main.index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@main.route('/logout')
def logout():
    user = session.pop('user', {})
    logger.info(f"User logged out: {user.get('username', 'unknown')}")
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


# ── Microsoft OAuth2 ──────────────────────────────────────────────────────────

@main.route('/microsoft_login')
def microsoft_login():
    session['oauth_state'] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        current_app.config['SCOPE'],
        state=session['oauth_state'],
        redirect_uri=url_for('main.get_token', _external=True),
    )
    logger.info("Redirecting to Microsoft login")
    return redirect(auth_url)


@main.route('/getAToken')
def get_token():
    # Validate state to prevent CSRF
    if request.args.get('state') != session.get('oauth_state'):
        logger.warning("OAuth state mismatch - possible CSRF attempt")
        flash('Authentication error. Please try again.', 'danger')
        return redirect(url_for('main.login'))

    if 'error' in request.args:
        logger.warning(f"OAuth error: {request.args.get('error_description')}")
        flash(f"Microsoft login error: {request.args.get('error_description')}", 'danger')
        return redirect(url_for('main.login'))

    code = request.args.get('code')
    result = _build_msal_app().acquire_token_by_authorization_code(
        code,
        scopes=current_app.config['SCOPE'],
        redirect_uri=url_for('main.get_token', _external=True),
    )

    if 'error' in result:
        logger.warning(f"Token acquisition error: {result.get('error_description')}")
        flash('Could not acquire token from Microsoft.', 'danger')
        return redirect(url_for('main.login'))

    claims = result.get('id_token_claims', {})
    ms_username = claims.get('preferred_username') or claims.get('email') or 'ms_user'
    session['user'] = {'username': ms_username, 'type': 'microsoft'}
    logger.info(f"Successful Microsoft login: {ms_username}")
    flash(f'Welcome, {ms_username}!', 'success')
    return redirect(url_for('main.index'))


# ── Articles ──────────────────────────────────────────────────────────────────

@main.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title  = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        body   = request.form.get('body', '').strip()
        image  = request.files.get('image')

        if not all([title, author, body]):
            flash('Title, author, and body are required.', 'warning')
            return render_template('create.html')

        image_url = ''
        if image and image.filename:
            try:
                image_url = upload_image(image)
            except Exception as e:
                logger.error(f"Image upload failed: {e}")
                flash('Image upload failed. Article saved without image.', 'warning')

        insert_article(title, author, body, image_url)
        logger.info(f"Article created: '{title}' by {session['user']['username']}")
        flash('Article created successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('create.html')


@main.route('/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit(article_id):
    article = get_article(article_id)
    if not article:
        flash('Article not found.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        title  = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        body   = request.form.get('body', '').strip()
        image  = request.files.get('image')

        image_url = article[4]  # keep existing URL by default
        if image and image.filename:
            try:
                image_url = upload_image(image)
            except Exception as e:
                logger.error(f"Image upload failed on edit: {e}")
                flash('Image upload failed. Keeping existing image.', 'warning')

        update_article(article_id, title, author, body, image_url)
        logger.info(f"Article {article_id} updated by {session['user']['username']}")
        flash('Article updated!', 'success')
        return redirect(url_for('main.index'))

    return render_template('edit.html', article=article)


@main.route('/delete/<int:article_id>', methods=['POST'])
@login_required
def delete(article_id):
    article = get_article(article_id)
    if article:
        if article[4]:
            delete_image(article[4])
        delete_article(article_id)
        logger.info(f"Article {article_id} deleted by {session['user']['username']}")
        flash('Article deleted.', 'info')
    return redirect(url_for('main.index'))
