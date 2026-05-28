import os

class Config:
    # Flask secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database backend: use sqlite locally, sqlserver on Azure.
    DATABASE_BACKEND = os.environ.get('DATABASE_BACKEND', 'sqlite').lower()
    SQLITE_DATABASE = os.environ.get('SQLITE_DATABASE') or 'cms_local.db'

    # Azure SQL Database. Set these in Azure App Service when DATABASE_BACKEND=sqlserver.
    SQL_SERVER = os.environ.get('SQL_SERVER', '')
    SQL_DATABASE = os.environ.get('SQL_DATABASE', '')
    SQL_USER_NAME = os.environ.get('SQL_USER_NAME', '')
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD', '')
    SQL_DRIVER = os.environ.get('SQL_DRIVER') or 'ODBC Driver 17 for SQL Server'
    SQL_TRUST_SERVER_CERTIFICATE = os.environ.get('SQL_TRUST_SERVER_CERTIFICATE', 'no')

    # Azure Blob Storage
    BLOB_ACCOUNT           = os.environ.get('BLOB_ACCOUNT')           or ''
    BLOB_CONTAINER         = os.environ.get('BLOB_CONTAINER')         or 'images'
    BLOB_STORAGE_KEY       = os.environ.get('BLOB_STORAGE_KEY')       or ''
    BLOB_CONNECTION_STRING = os.environ.get('BLOB_CONNECTION_STRING') or (
        f'DefaultEndpointsProtocol=https;AccountName={BLOB_ACCOUNT};'
        f'AccountKey={BLOB_STORAGE_KEY};'
        'EndpointSuffix=core.windows.net'
    )
    IMAGE_UPLOAD_BACKEND = os.environ.get(
        'IMAGE_UPLOAD_BACKEND',
        'local' if DATABASE_BACKEND == 'sqlite' else 'blob'
    ).lower()
    LOCAL_UPLOAD_FOLDER = os.environ.get('LOCAL_UPLOAD_FOLDER') or 'uploads'

    # Microsoft Entra ID / OAuth2
    CLIENT_ID     = os.environ.get('CLIENT_ID')     or '1660e7a3-74ae-4945-aea0-5bd962871c33'
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET') or '<YOUR_CLIENT_SECRET>'
    AUTHORITY     = 'https://login.microsoftonline.com/common'
    REDIRECT_PATH = '/getAToken'
    SCOPE         = ['User.Read']
