import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core.config import Settings
from core.database import get_db_session
from main import app
from services.user_service import get_or_create_user


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.settings = patch('core.auth.get_settings', return_value=Settings(
            _env_file=None, auth0_domain='test.auth0.com', auth0_audience='https://run-tib-api',
        ))
        self.settings.start()
        self.keys = patch('core.auth.jwks_client')
        self.key_client = self.keys.start().return_value
        self.key_client.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.key.public_key())
        self.session = AsyncMock()
        self.user = SimpleNamespace(id=uuid4(), auth0_subject='google-oauth2|123',
                                    email='runner@example.com', display_name='Runner',
                                    avatar_url=None, is_active=True)
        self.session.scalar.return_value = self.user

        async def session_override():
            yield self.session

        app.dependency_overrides[get_db_session] = session_override
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.keys.stop()
        self.settings.stop()

    def token(self, **changes):
        claims = dict(sub='google-oauth2|123', iss='https://test.auth0.com/',
                      aud='https://run-tib-api', iat=int(time.time()) - 1,
                      exp=int(time.time()) + 300)
        claims.update(changes)
        return jwt.encode(claims, self.key, algorithm='RS256', headers={'kid': 'test'})

    def me(self, token):
        return self.client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})

    def test_missing_token(self):
        response = self.client.get('/api/v1/auth/me')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers['www-authenticate'], 'Bearer')
        self.session.scalar.assert_not_awaited()

    def test_valid_access_token(self):
        response = self.me(self.token())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], str(self.user.id))
        self.assertNotIn('auth0_subject', response.json())

    def test_invalid_claims(self):
        for change in [dict(exp=1), dict(iss='https://other.auth0.com/'),
                       dict(aud='spa-client-id'), dict(sub='client@clients'),
                       dict(nbf=int(time.time()) + 300), dict(sub='')]:
            with self.subTest(change=change):
                self.assertEqual(self.me(self.token(**change)).status_code, 401)
        self.session.scalar.assert_not_awaited()

    def test_bad_signature_and_algorithm(self):
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        claims = jwt.decode(self.token(), options={'verify_signature': False})
        for token in ['not-a-jwt', jwt.encode(claims, other_key, algorithm='RS256'),
                      jwt.encode(claims, 'x' * 64, algorithm='HS256')]:
            with self.subTest(token=token[:12]):
                self.assertEqual(self.me(token).status_code, 401)

    def test_missing_expiration(self):
        claims = jwt.decode(self.token(), options={'verify_signature': False})
        del claims['exp']
        self.assertEqual(self.me(jwt.encode(claims, self.key, algorithm='RS256')).status_code, 401)

    def test_disabled_user(self):
        self.user.is_active = False
        self.assertEqual(self.me(self.token()).status_code, 403)

    def test_missing_configuration(self):
        with patch('core.auth.get_settings', return_value=Settings(_env_file=None, auth0_domain='', auth0_audience='')):
            self.assertEqual(self.me(self.token()).status_code, 503)

    def test_jwks_outage(self):
        from jwt.exceptions import PyJWKClientConnectionError
        self.key_client.get_signing_key_from_jwt.side_effect = PyJWKClientConnectionError('offline')
        self.assertEqual(self.me(self.token()).status_code, 503)

    def test_rejected_token_is_logged_without_credentials(self):
        token = self.token(aud='wrong-audience')
        with self.assertLogs('uvicorn.error', level='WARNING') as captured:
            response = self.me(token)
        logs = '\n'.join(captured.output)
        self.assertIn('InvalidAudienceError', logs)
        self.assertIn(response.headers['x-request-id'], logs)
        self.assertNotIn(token, logs)

    def test_database_failure_has_safe_diagnostic_and_request_id(self):
        from sqlalchemy.exc import OperationalError
        self.session.scalar.side_effect = OperationalError('SELECT secret', {'password': 'never-log-this'}, Exception('private-details'))
        with self.assertLogs('uvicorn.error.api', level='ERROR') as captured:
            response = self.me(self.token())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['request_id'], response.headers['x-request-id'])
        logs = '\n'.join(captured.output)
        self.assertIn('OperationalError', logs)
        self.assertNotIn('never-log-this', logs)
        self.assertNotIn('private-details', logs)

    def test_swagger_supports_only_manual_bearer(self):
        schema = self.client.get('/openapi.json').json()
        schemes = schema['components']['securitySchemes']
        self.assertEqual(set(schemes), {'HTTPBearer'})
        self.assertEqual(schemes['HTTPBearer']['scheme'], 'bearer')
        security = schema['paths']['/api/v1/auth/me']['get']['security']
        self.assertEqual(security, [{'HTTPBearer': []}])
        self.assertIsNone(app.swagger_ui_init_oauth)
        self.assertEqual(self.client.get('/docs/oauth2-redirect').status_code, 404)

    def test_challenge_creation_requires_permission(self):
        body = dict(name='Test', starts_at='2026-11-01T00:00:00Z', ends_at='2026-12-01T00:00:00Z')
        self.assertEqual(self.client.post('/api/v1/challenges', json=body).status_code, 401)
        response = self.client.post('/api/v1/challenges', json=body,
                                    headers={'Authorization': f'Bearer {self.token()}'})
        self.assertEqual(response.status_code, 403)
        with patch('api.challenges.challenge_service.create_challenge', new_callable=AsyncMock) as create:
            create.return_value = dict(id=uuid4(), **body, description=None, status='draft',
                                       created_at='2026-10-04T00:00:00Z', updated_at='2026-10-04T00:00:00Z')
            response = self.client.post('/api/v1/challenges', json=body, headers={
                'Authorization': f'Bearer {self.token(permissions=["create:challenges"])}'})
            self.assertEqual(response.status_code, 201)
            create.assert_awaited_once()


class ProvisioningTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_user_is_created_from_verified_profile(self):
        session = AsyncMock()
        user = SimpleNamespace(is_active=True)
        session.scalar.side_effect = [None, user]
        profile = {'sub': 'google-oauth2|123', 'email': 'runner@example.com', 'name': 'Runner'}
        with patch('services.user_service.httpx.AsyncClient') as client:
            response = MagicMock()
            response.json.return_value = profile
            client.return_value.__aenter__.return_value.get = AsyncMock(return_value=response)
            self.assertIs(await get_or_create_user(session, profile['sub'], 'access-token'), user)
        session.execute.assert_awaited_once()
        session.commit.assert_awaited_once()
        # Concurrent first-login requests use the unique Auth0 subject conflict target.
        statement = str(session.execute.call_args.args[0])
        self.assertIn('ON CONFLICT (auth0_subject) DO NOTHING', statement)

    async def test_mismatched_profile_does_not_create_user(self):
        session = AsyncMock()
        session.scalar.return_value = None
        with patch('services.user_service.httpx.AsyncClient') as client:
            response = MagicMock()
            response.json.return_value = {'sub': 'google-oauth2|someone-else'}
            client.return_value.__aenter__.return_value.get = AsyncMock(return_value=response)
            with self.assertRaises(HTTPException) as raised:
                await get_or_create_user(session, 'google-oauth2|123', 'access-token')
            self.assertEqual(raised.exception.status_code, 401)
        session.execute.assert_not_awaited()

    async def test_existing_disabled_user_is_rejected_without_profile_request(self):
        session = AsyncMock()
        session.scalar.return_value = SimpleNamespace(is_active=False)
        with patch('services.user_service.httpx.AsyncClient') as client:
            with self.assertRaises(HTTPException) as raised:
                await get_or_create_user(session, 'google-oauth2|123', 'access-token')
            self.assertEqual(raised.exception.status_code, 403)
            client.assert_not_called()


class CertificateTests(unittest.TestCase):
    def test_jwks_uses_verified_certificate_bundle(self):
        import ssl
        from core.auth import jwks_client
        jwks_client.cache_clear()
        with patch('core.auth.PyJWKClient') as constructor:
            jwks_client('https://certificate-test.auth0.com/')
            context = constructor.call_args.kwargs['ssl_context']
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            self.assertGreater(context.cert_store_stats()['x509_ca'], 0)
        jwks_client.cache_clear()
