"""
conftest.py — pytest session-level setup for Case-Verify AI tests.

Provides lightweight stubs for optional heavy dependencies
(google-generativeai, streamlit, passlib, bcrypt, sqlalchemy, etc.)
so the core business-logic modules can be imported and tested in a
minimal environment without installing the full production dependency tree.
"""
import sys
import types
import unittest.mock as mock

# ---------------------------------------------------------------------------
# Stub: google-generativeai
# ---------------------------------------------------------------------------
_google_ns = types.ModuleType("google")
_genai_mod = types.ModuleType("google.generativeai")

class _FakeGenerativeModel:
    def __init__(self, *a, **kw):
        pass
    def generate_content(self, *a, **kw):
        r = mock.MagicMock()
        r.text = '{"cause": "stub", "start_date": "2024-01-01"}'
        return r

_genai_mod.configure = mock.MagicMock()
_genai_mod.GenerativeModel = _FakeGenerativeModel

_google_ns.generativeai = _genai_mod
sys.modules.setdefault("google", _google_ns)
sys.modules.setdefault("google.generativeai", _genai_mod)

# ---------------------------------------------------------------------------
# Stub: python-dotenv
# ---------------------------------------------------------------------------
_dotenv_mod = types.ModuleType("dotenv")
_dotenv_mod.load_dotenv = mock.MagicMock(return_value=True)
sys.modules.setdefault("dotenv", _dotenv_mod)

# ---------------------------------------------------------------------------
# Stub: streamlit  (only needed by auth/authenticator.py + app.py)
# ---------------------------------------------------------------------------
_st_mod = types.ModuleType("streamlit")
_st_session_state: dict = {}
_st_mod.session_state = _st_session_state  # type: ignore[attr-defined]
_st_mod.warning = mock.MagicMock()
_st_mod.success = mock.MagicMock()
_st_mod.error = mock.MagicMock()
_st_mod.info = mock.MagicMock()
sys.modules.setdefault("streamlit", _st_mod)

# ---------------------------------------------------------------------------
# Stub: passlib (used in auth/authenticator.py via passlib.hash.bcrypt)
# ---------------------------------------------------------------------------
_passlib_mod = types.ModuleType("passlib")
_passlib_hash = types.ModuleType("passlib.hash")

class _FakeBcrypt:
    @staticmethod
    def hash(password: str) -> str:
        return f"$2b$12$fakehash_{password[:8]}"
    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        return hashed == f"$2b$12$fakehash_{password[:8]}"

_passlib_hash.bcrypt = _FakeBcrypt()
_passlib_mod.hash = _passlib_hash  # type: ignore[attr-defined]
sys.modules.setdefault("passlib", _passlib_mod)
sys.modules.setdefault("passlib.hash", _passlib_hash)

# ---------------------------------------------------------------------------
# Stub: bcrypt  (used in auth/user_manager.py)
# ---------------------------------------------------------------------------
_bcrypt_mod = types.ModuleType("bcrypt")
_bcrypt_mod.hashpw = mock.MagicMock(return_value=b"$2b$12$fakehash")  # type: ignore[attr-defined]
_bcrypt_mod.checkpw = mock.MagicMock(return_value=True)               # type: ignore[attr-defined]
_bcrypt_mod.gensalt = mock.MagicMock(return_value=b"$2b$12$fakesalt") # type: ignore[attr-defined]
sys.modules.setdefault("bcrypt", _bcrypt_mod)

# ---------------------------------------------------------------------------
# Stub: sqlalchemy  (used in database/)
# ---------------------------------------------------------------------------
def _stub_sqlalchemy():
    sa = types.ModuleType("sqlalchemy")
    sa.create_engine = mock.MagicMock()
    sa.Column = mock.MagicMock()
    sa.Integer = mock.MagicMock()
    sa.String = mock.MagicMock()
    sa.Boolean = mock.MagicMock()
    sa.DateTime = mock.MagicMock()
    sa.Text = mock.MagicMock()
    sa.JSON = mock.MagicMock()
    sa.Float = mock.MagicMock()
    sa.ForeignKey = mock.MagicMock()
    sa.event = mock.MagicMock()

    # declarative_base must return a *real* Python class so that subclasses
    # (User, Case, …) are proper types. Python 3.13 tightens Optional[T]
    # validation and rejects MagicMock instances as type arguments.
    class _StubBase:
        __tablename__ = ""
        metadata = mock.MagicMock()

    def _declarative_base(*args, **kwargs):  # noqa: D401
        return _StubBase

    orm = types.ModuleType("sqlalchemy.orm")
    orm.sessionmaker = mock.MagicMock()
    orm.declarative_base = _declarative_base
    orm.relationship = mock.MagicMock()
    orm.Session = mock.MagicMock()

    ext = types.ModuleType("sqlalchemy.ext")
    ext_dec = types.ModuleType("sqlalchemy.ext.declarative")
    ext_dec.declarative_base = _declarative_base
    ext.declarative = ext_dec

    pool = types.ModuleType("sqlalchemy.pool")
    pool.StaticPool = mock.MagicMock()

    sql = types.ModuleType("sqlalchemy.sql")
    sql.func = mock.MagicMock()

    sys.modules.setdefault("sqlalchemy", sa)
    sys.modules.setdefault("sqlalchemy.orm", orm)
    sys.modules.setdefault("sqlalchemy.ext", ext)
    sys.modules.setdefault("sqlalchemy.ext.declarative", ext_dec)
    sys.modules.setdefault("sqlalchemy.pool", pool)
    sys.modules.setdefault("sqlalchemy.sql", sql)

_stub_sqlalchemy()
