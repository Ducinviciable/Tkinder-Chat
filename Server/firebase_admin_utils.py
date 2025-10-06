import os
import json

try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth
    _FIREBASE_AVAILABLE = True
except Exception:
    _FIREBASE_AVAILABLE = False

_firebase_initialized = False


def init_firebase_if_needed() -> None:
    global _firebase_initialized
    if _firebase_initialized or not _FIREBASE_AVAILABLE:
        return
    try:
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            default_sa_path = os.path.join(project_root, 'lib', 'firebase-service.json')
            if os.path.isfile(default_sa_path):
                project_id = ''
                try:
                    with open(default_sa_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        project_id = (data.get('project_id') or '').strip()
                except Exception:
                    project_id = ''
                cred = credentials.Certificate(default_sa_path)
                if project_id:
                    firebase_admin.initialize_app(cred, {'projectId': project_id})
                else:
                    firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                print('[Auth] Firebase initialized from Chat/lib/firebase-service.json')
                return
        except Exception as e:
            print(f"[Auth] Failed to init from Chat/lib/firebase-service.json: {e}")

        # Try JSON from environment variable
        firebase_service_account_key = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', '').strip()
        if firebase_service_account_key:
            try:
                cred_data = json.loads(firebase_service_account_key)
                cred = credentials.Certificate(cred_data)
                project_id = cred_data.get('project_id', '')
                if project_id:
                    firebase_admin.initialize_app(cred, {'projectId': project_id})
                else:
                    firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                print('[Auth] Firebase initialized from environment variable')
                return
            except Exception as e:
                print(f"[Auth] Failed to parse FIREBASE_SERVICE_ACCOUNT_KEY: {e}")

        # Fallback to file path from env
        cred_path = os.environ.get('FIREBASE_CREDENTIALS', '').strip() or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '').strip()
        if cred_path and os.path.isfile(cred_path):
            project_id = ''
            try:
                with open(cred_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    project_id = (data.get('project_id') or '').strip()
            except Exception:
                project_id = ''
            cred = credentials.Certificate(cred_path)
            if project_id:
                firebase_admin.initialize_app(cred, {'projectId': project_id})
            else:
                firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print('[Auth] Firebase initialized from file')
            return

        # Default application credentials
        firebase_admin.initialize_app()
        _firebase_initialized = True
        print('[Auth] Firebase initialized with default credentials')
    except Exception as exc:
        print(f"[Auth] Firebase init failed: {exc}")
        print('[Auth] Please set FIREBASE_SERVICE_ACCOUNT_KEY or GOOGLE_APPLICATION_CREDENTIALS')
        _firebase_initialized = False


def verify_id_token(id_token: str) -> tuple[bool, str]:
    if not _FIREBASE_AVAILABLE:
        return False, 'auth_unavailable'
    init_firebase_if_needed()
    if not _firebase_initialized:
        return False, 'auth_not_initialized'
    try:
        decoded = fb_auth.verify_id_token(id_token, check_revoked=True, clock_skew_seconds=60)
        email = decoded.get('email') or ''
        name = decoded.get('name') or ''
        uid = decoded.get('uid') or 'unknown'
        label = email or name or uid
        return True, label
    except Exception as exc:
        reason = f'invalid_token: {exc}'
        print(f"[Auth] Token verify failed: {reason}")
        return False, reason


def get_user_by_email(email: str) -> dict | None:
    if not _FIREBASE_AVAILABLE:
        return None
    init_firebase_if_needed()
    if not _firebase_initialized:
        return None
    try:
        user_record = fb_auth.get_user_by_email(email)
        return {
            'uid': user_record.uid or '',
            'email': email,
            'displayName': user_record.display_name or ''
        }
    except Exception:
        return None


