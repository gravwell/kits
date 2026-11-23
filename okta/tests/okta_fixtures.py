#!/usr/bin/env python3
"""Synthetic Okta System Log fixtures and a regression check for every Okta kit detection.

Every case is a handful of hand-written Okta events placed in its own 15-minute window
(case N covers FIXTURE_DAY + N hours, minutes 00-15), the same window shape the kit's
scheduled searches use. The check finds every detection that returns rows in each case
window and compares that set with the case's `expect` list, so it catches both missed
detections and detections firing on the wrong events (see check() for how).

All data is synthetic: example.com / example.net names, documentation IP ranges
(192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24), private-use AS numbers, made-up IDs.

Usage (the kit must be installed on the instance; GRAVWELL_URL / GRAVWELL_TOKEN set):
  python3 okta_fixtures.py build              # write fixtures.jsonl (raw Okta events, one per line)
  python3 okta_fixtures.py ingest             # import fixtures.jsonl into tag okta-fixtures
  python3 okta_fixtures.py check [-j 6] [--full] [CASE...]

`check` reads the detection queries from this kit directory and points them at the
fixture tag by replacing the config macro $OKTA (the System Log tag). The queries use no other
macros. Ingest once per tag: re-importing
duplicates the events and the "below threshold" cases would then fire. After changing the
fixtures, ingest into a new tag (OKTA_FIXTURE_TAG=okta-fixtures2 for ingest and check).
"""
import argparse
import concurrent.futures as cf
import csv
import glob
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from base64 import b64encode
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, 'fixtures.jsonl')
TAG = os.environ.get('OKTA_FIXTURE_TAG', 'okta-fixtures')
FIXTURE_DAY = datetime(2026, 1, 5, tzinfo=timezone.utc)
WINDOW = timedelta(minutes=15)
DOMAIN = 'example.com'

# ---------------------------------------------------------------------------------------------
# event builder
# ---------------------------------------------------------------------------------------------

GEO = {
    'United States': ('Denver', 'Colorado', '80202', 39.74, -104.99),
    'Germany': ('Berlin', 'Land Berlin', '10115', 52.52, 13.40),
    'Brazil': ('Sao Paulo', 'Sao Paulo', '01000', -23.55, -46.63),
}

MESSAGES = {
    'user.session.start': 'User login to Okta',
    'user.session.access_admin_app': 'User accessing Okta admin app',
    'user.authentication.sso': 'User single sign on to app',
    'user.authentication.auth_via_mfa': 'Authentication of user via MFA',
    'user.authentication.auth_via_IDP': 'Authenticate user via IDP',
    'system.push.send_factor_verify_push': 'Push notification sent for user verification',
    'user.mfa.okta_verify.deny_push': 'User rejected Okta push verify',
    'user.account.lock': 'Max sign in attempts exceeded',
    'user.account.lock.limit': 'User account has reached the lockout limit',
    'policy.evaluate_sign_on': 'Evaluation of sign-on policy',
}


def tgt(ttype, tid, alt=None, name=None):
    """One target object, serialized in Okta's key order (id, type, alternateId, displayName, detailEntry)."""
    return {'id': tid, 'type': ttype, 'alternateId': alt, 'displayName': name, 'detailEntry': None}


def user_target(login, name=None):
    return tgt('User', '00u' + hashlib.sha1(login.encode()).hexdigest()[:17], f'{login}@{DOMAIN}', name or login.title())


def app_target(name, alt='fixtureapp'):
    return tgt('AppInstance', '0oa' + hashlib.sha1(name.encode()).hexdigest()[:17], alt, name)


class Case:
    def __init__(self, name, expect, doc):
        self.name, self.expect, self.doc = name, sorted(expect), doc
        self.events = []
        self.index = None

    @property
    def start(self):
        return FIXTURE_DAY + timedelta(hours=self.index)

    def ev(self, event_type, at=2, actor='alice', actor_type='User', ip='192.0.2.10', country='United States',
           result='SUCCESS', reason=None, severity='INFO', proxy=False, risk=None, device='Computer',
           session=None, root_session=None, debug=None, targets=None, message=None, raw_target=None):
        """Add an event `at` minutes after the window start (negative = history before the window).

        History events are placed at :35 of an hour (at = -25, -60*k - 25, ...) so they never fall
        inside any case's window.
        """
        n = len(self.events)
        published = self.start + timedelta(minutes=at, seconds=n)
        uid = hashlib.sha1(f'{self.name}/{n}'.encode()).hexdigest()
        # actor: a login without domain ("alice" -> alice@example.com); "!text" = use text verbatim as alternateId
        if actor.startswith('!'):
            alt, display = actor[1:], 'unknown'
        elif actor_type == 'User' and actor != 'unknown':
            alt, display = f'{actor}@{DOMAIN}', actor.title()
        else:
            alt, display = actor, actor
        actor_obj = {
            'id': ('00u' if actor_type == 'User' else '0oa') + hashlib.sha1(actor.encode()).hexdigest()[:17],
            'type': actor_type, 'alternateId': alt, 'displayName': display, 'detailEntry': None,
        }
        city, state, postal, lat, lon = GEO[country]
        geo = {'city': city, 'state': state, 'country': country, 'postalCode': postal,
               'geolocation': {'lat': lat, 'lon': lon}}
        sid = session or f'idx{uid[:22]}'
        security = {'asNumber': 64496, 'asOrg': 'example networks', 'isp': 'example isp', 'domain': 'example.net',
                    'isProxy': proxy}
        if risk:
            security['risk'] = risk
        dd = {'requestId': f'fixture-{uid[:16]}', 'requestUri': '/idp/idx/identify', 'url': '/idp/idx/identify?'}
        dd.update(debug or {})
        e = {
            'actor': actor_obj,
            'client': {'userAgent': {'rawUserAgent': 'Mozilla/5.0 (fixture)', 'os': 'Mac OS X', 'browser': 'CHROME'},
                       'zone': 'null', 'device': device, 'id': None, 'ipAddress': ip, 'geographicalContext': geo},
            'device': None,
            'authenticationContext': {'authenticationProvider': None, 'credentialProvider': None,
                                      'credentialType': None, 'issuer': None, 'interface': None,
                                      'authenticationStep': 0, 'rootSessionId': root_session or sid,
                                      'externalSessionId': sid},
            'displayMessage': message or MESSAGES.get(event_type, 'Synthetic fixture event'),
            'eventType': event_type,
            'outcome': {'result': result, 'reason': reason},
            'published': published.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'securityContext': security,
            'severity': severity,
            'debugContext': {'debugData': dd},
            'legacyEventType': None,
            'transaction': {'type': 'WEB', 'id': f'fixture-{uid[16:32]}', 'detail': {}},
            'uuid': f'{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:32]}',
            'version': '0',
            'request': {'ipChain': [{'ip': ip, 'geographicalContext': geo, 'version': 'V4', 'source': None}]},
            'target': targets,
        }
        line = json.dumps(e, separators=(',', ':'))
        if raw_target is not None:
            line = line.replace('"target":null', '"target":' + raw_target)
        self.events.append(line)
        return self


def failed_signin(c, actor, ip, dt_hash, at=2, **kw):
    return c.ev('user.session.start', at=at, actor=actor, ip=ip, result='FAILURE', reason='INVALID_CREDENTIALS',
                severity='WARN', debug={'dtHash': dt_hash}, **kw)


def dt(label):
    return hashlib.sha256(label.encode()).hexdigest()


# ---------------------------------------------------------------------------------------------
# cases: name, detections expected to fire in the case window, description
# ---------------------------------------------------------------------------------------------

ADMIN_CONSOLE = 'Okta Admin Console'
CASES = []


def case(name, expect, doc):
    c = Case(name, expect, doc)
    c.index = len(CASES)
    CASES.append(c)
    return c


MOD = 'Risk-Scored Modification Feed'

c = case('baseline-normal-signin', [], 'Ordinary successful sign-in, SSO and MFA: nothing fires')
c.ev('user.session.start', actor='base01', session='idxbase01')
c.ev('user.authentication.auth_via_mfa', at=3, actor='base01', session='idxbase01')
c.ev('user.authentication.sso', at=4, actor='base01', session='idxbase01', targets=[app_target('Fixture Wiki')])

c = case('admin-console-via-proxy', ['Okta Admin Console Access via Anonymizing Proxy', 'Okta Admin Console Access from a New IP'],
         'Admin Console reached through an anonymizing proxy (and from an IP this admin never used for it)')
c.ev('user.session.access_admin_app', actor='admin02', ip='203.0.113.2', proxy=True,
     risk={'level': 'MEDIUM', 'reasons': 'Anonymizing Proxy'}, targets=[app_target(ADMIN_CONSOLE, 'Okta Admin Console')])

c = case('admin-console-known-ip', [], 'Admin Console from an IP this admin used 2 days earlier: not new')
c.ev('user.session.access_admin_app', at=-2 * 24 * 60 - 25, actor='admin03', ip='192.0.2.3', targets=[app_target(ADMIN_CONSOLE, 'Okta Admin Console')])
c.ev('user.session.access_admin_app', actor='admin03', ip='192.0.2.3', targets=[app_target(ADMIN_CONSOLE, 'Okta Admin Console')])

c = case('admin-console-new-ip', ['Okta Admin Console Access from a New IP'], 'Admin Console from a new IP; the admin used another IP 2 days earlier')
c.ev('user.session.access_admin_app', at=-2 * 24 * 60 - 25, actor='admin04', ip='192.0.2.4', targets=[app_target(ADMIN_CONSOLE, 'Okta Admin Console')])
c.ev('user.session.access_admin_app', actor='admin04', ip='198.51.100.4', targets=[app_target(ADMIN_CONSOLE, 'Okta Admin Console')])

c = case('session-start-via-proxy', ['Okta Session Start via Anonymizing Proxy'], 'Successful sign-in through an anonymizing proxy')
c.ev('user.session.start', actor='user05', ip='203.0.113.5', proxy=True)

c = case('dos-rate-limit', ['Possible Okta DoS Attack'], 'Org rate limit violation')
c.ev('system.org.rate_limit.violation', actor='Okta System', actor_type='SystemPrincipal', ip='192.0.2.6',
     severity='WARN', message='Rate limit violation')

c = case('idp-saml-failure', ['Okta Sign-In Events via Third-Party IdP'], 'Inbound SAML sign-in rejected by Okta')
c.ev('user.authentication.auth_via_IDP', actor='user07', ip='198.51.100.7', result='FAILURE',
     reason='Unable to validate SAML Response', debug={'requestUri': '/oauth2/aus0fixture07/v1/authorize/callback'})

c = case('threatinsight-suspected', ['Okta ThreatInsight Threat Suspected Promotion'], 'Sign-in Okta ThreatInsight flagged (threatSuspected=true)')
c.ev('user.session.start', actor='user08', ip='203.0.113.8', result='FAILURE', reason='VERIFICATION_ERROR',
     debug={'threatSuspected': 'true'})

c = case('api-token-created', ['Okta API Token Created', MOD], 'API token created')
c.ev('system.api_token.create', actor='admin09', targets=[tgt('Token', '00Tfixture09', None, 'fixture-token-09')])

c = case('api-token-revoked', ['Okta API Token Revoked', MOD], 'API token revoked')
c.ev('system.api_token.revoke', actor='admin10', targets=[tgt('Token', '00Tfixture10', None, 'fixture-token-10')])

c = case('fastpass-phishing', ['Okta FastPass Phishing Detection'], 'FastPass refused to sign in to a phishing origin')
c.ev('user.authentication.auth_via_mfa', actor='user11', result='FAILURE', reason='FastPass declined phishing attempt')

c = case('network-zone-updated', ['Okta Network Zone Modified, Deactivated or Deleted', MOD], 'Network zone updated')
c.ev('zone.update', actor='admin12', targets=[tgt('Zone', 'nzofixture12', None, 'Fixture Office Zone')])

c = case('unauthorized-scope-client-credentials', ['Unauthorized Scope for Public App OAuth2 Token Grant with Client Credentials'],
         'Client-credentials token request for a scope the client is not granted')
c.ev('app.oauth2.as.token.grant', actor='fixture-service-13', actor_type='PublicClientApp', ip='198.51.100.13',
     result='FAILURE', reason='no_matching_scope', debug={'grantType': 'client_credentials'})

c = case('admin-role-to-new-user', ['Okta Admin Role Granted to a New User', 'Okta Admin Role Assigned to a User or Group', MOD],
         'Admin role granted to an account created 2 hours earlier')
c.ev('user.lifecycle.create', at=-2 * 60 - 25, actor='admin14', targets=[user_target('newhire14')])
c.ev('user.account.privilege.grant', actor='admin14', targets=[user_target('newhire14')],
     message='Grant user privilege')

c = case('admin-role-to-existing-user', ['Okta Admin Role Assigned to a User or Group', MOD],
         'Admin role granted to an account created 2 days earlier: not "new"')
c.ev('user.lifecycle.create', at=-2 * 24 * 60 - 25, actor='admin15', targets=[user_target('staff15')])
c.ev('user.account.privilege.grant', actor='admin15', targets=[user_target('staff15')], message='Grant user privilege')

c = case('admin-role-to-group', ['Okta Admin Role Assigned to a User or Group', MOD], 'Admin role granted to a group')
c.ev('group.privilege.grant', actor='admin16', targets=[tgt('UserGroup', '00gfixture16', None, 'Fixture Helpdesk')],
     message='Grant group privilege')

c = case('unauthorized-app-access', ['Unauthorized Access to an Okta Application'], 'User tried to open an app they are not assigned')
c.ev('app.generic.unauth_app_access_attempt', actor='user17', result='FAILURE', targets=[app_target('Fixture Payroll')])

c = case('many-device-tokens-one-ip', ['Okta Many Device Tokens from One IP on Failed Sign-Ins', 'Okta Password Spray from One IP'],
         '10 failed sign-ins from one IP with 10 different device tokens (10 users, so it is also a spray)')
for i in range(10):
    failed_signin(c, f'user18{i:02d}', '203.0.113.18', dt(f'case18-{i}'), at=2 + i // 2)

c = case('brute-force-one-account', ['Okta Brute Force Against One Account'], '5 failed sign-ins for one user')
for i in range(5):
    failed_signin(c, 'user19', '198.51.100.19', dt('case19'), at=2 + i)

c = case('brute-force-below-threshold', [], '4 failed sign-ins for one user: below the threshold of 5')
for i in range(4):
    failed_signin(c, 'user20', '198.51.100.20', dt('case20'), at=2 + i)

c = case('password-spray-one-ip', ['Okta Password Spray from One IP'], 'One IP fails sign-in for 3 different users')
for i in range(3):
    failed_signin(c, f'user21{i}', '203.0.113.21', dt(f'case21-{i}'), at=2 + i)

c = case('password-spray-below-threshold', [], 'One IP fails sign-in for 2 users: below the threshold of 3')
for i in range(2):
    failed_signin(c, f'user22{i}', '203.0.113.22', dt(f'case22-{i}'), at=2 + i)

c = case('password-spray-one-device', ['Okta Password Spray from One Device'], 'One device token fails sign-in for 3 users from 3 IPs')
for i in range(3):
    failed_signin(c, f'user23{i}', f'198.51.100.{230 + i}', dt('case23'), at=2 + i)

c = case('same-device-behind-proxy', ['Multiple Okta Users Authenticating from the Same Device Behind a Proxy', 'Okta Session Start via Anonymizing Proxy'],
         'Two users sign in from the same device token through an anonymizing proxy')
for i in range(2):
    c.ev('user.session.start', at=2 + i, actor=f'user24{i}', ip='203.0.113.24', proxy=True, debug={'dtHash': dt('case24')})

c = case('sensitive-scope-granted', ['Sensitive Okta OAuth Scope Granted to an App'], 'Admin consent for okta.users.manage (with harmless scopes in the same grant)')
c.ev('app.oauth2.admin.consent.grant', actor='admin25', targets=[
    app_target('Fixture Integration 25'),
    tgt('ConsentGrant', 'oagfixture25a', None, 'openid'),
    tgt('ConsentGrant', 'oagfixture25b', None, 'okta.users.manage'),
], message='Admin consent granted')

c = case('harmless-scope-granted', [], 'Admin consent for scopes that only look sensitive (okta.users.read.self, okta.myAccount.manage)')
c.ev('app.oauth2.admin.consent.grant', actor='admin26', targets=[
    app_target('Fixture Integration 26'),
    tgt('ConsentGrant', 'oagfixture26a', None, 'okta.users.read.self'),
    tgt('ConsentGrant', 'oagfixture26b', None, 'okta.myAccount.manage'),
], message='Admin consent granted')

c = case('policy-updated', ['Okta Policy Modified, Deactivated or Deleted', MOD], 'Sign-on policy updated')
c.ev('policy.lifecycle.update', actor='admin27', targets=[tgt('PolicyEntity', '00pfixture27', None, 'Fixture Sign-On Policy')])

c = case('sessions-from-two-countries', ['Okta User Sessions Started from Different Geolocations', 'Multiple Okta Sessions for One User from Different IPs'],
         'One user starts sessions in the United States and in Germany within the window (2 sessions, 2 IPs)')
c.ev('user.session.start', at=2, actor='user28', ip='192.0.2.28', session='idxcase28a')
c.ev('user.session.start', at=9, actor='user28', ip='198.51.100.28', country='Germany', session='idxcase28b')

c = case('user-created', ['New Okta User Created'], 'New user created')
c.ev('user.lifecycle.create', actor='admin29', targets=[user_target('newhire29')])

c = case('target-key-order-changed', ['Target Key Order Changed'], 'An event whose target objects are not serialized id,type,alternateId,displayName')
c.ev('user.account.update_profile', actor='admin30', message='Update user profile for Okta',
     raw_target='[{"type":"User","id":"00ufixture30","alternateId":"user30@example.com","displayName":"User30","detailEntry":null}]')

c = case('mfa-factor-deactivated', ['Okta MFA Reset or Deactivated', MOD], 'Admin deactivates a user\'s MFA factor')
c.ev('user.mfa.factor.deactivate', actor='admin31', targets=[user_target('user31')], message='Reset factor for user')

c = case('admin-console-new-behaviours', ['Okta New Admin Console Behaviours'], 'Admin Console sign-on policy evaluation with New Device / New IP')
c.ev('policy.evaluate_sign_on', actor='admin32', targets=[app_target(ADMIN_CONSOLE, 'Okta Admin Console')],
     debug={'behaviors': '{New Geo-Location=NEGATIVE, New Device=POSITIVE, New IP=POSITIVE, New State=NEGATIVE, New Country=NEGATIVE, Velocity=NEGATIVE, New City=NEGATIVE}'})

c = case('oauth-client-secret-read', ['Okta OAuth Client Secret or Credential Accessed or Created'], 'OAuth client secret read')
c.ev('app.oauth2.client.read_client_secret', actor='admin33', targets=[app_target('Fixture Integration 33')])

c = case('signin-high-risk', ['Okta Sign-In with Elevated Risk or New Behavior'], 'Sign-in Okta rated HIGH risk')
c.ev('user.session.start', actor='user34', risk={'level': 'HIGH', 'reasons': 'New Device, New Geo-Location'},
     debug={'behaviors': '{New Geo-Location=POSITIVE, New Device=POSITIVE, New IP=POSITIVE, New State=NEGATIVE, New Country=NEGATIVE, Velocity=NEGATIVE, New City=POSITIVE}'})

c = case('mfa-push-bombing', ['Potential Okta MFA Bombing via Push Notifications'], '5 Okta Verify pushes to one user, none answered')
for i in range(5):
    c.ev('system.push.send_factor_verify_push', at=2 + i, actor='user35')

c = case('mfa-push-bombing-accepted', ['Potential Okta MFA Bombing via Push Notifications', 'Potentially Successful Okta MFA Bombing via Push Notifications'],
         '3 pushes, 2 denied, then the user accepts one')
for i in range(3):
    c.ev('system.push.send_factor_verify_push', at=2 + i, actor='user36')
for i in range(2):
    c.ev('user.mfa.okta_verify.deny_push', at=2 + i, actor='user36', result='FAILURE')
c.ev('user.authentication.auth_via_mfa', at=6, actor='user36')

c = case('mfa-push-below-threshold', [], '4 pushes and 1 denial: below both thresholds')
for i in range(4):
    c.ev('system.push.send_factor_verify_push', at=2 + i, actor='user37')
c.ev('user.mfa.okta_verify.deny_push', at=3, actor='user37', result='FAILURE')

c = case('two-sessions-two-ips', ['Multiple Okta Sessions for One User from Different IPs'], 'One user starts 2 sessions from 2 IPs in the same country')
c.ev('user.session.start', at=2, actor='user38', ip='192.0.2.38', session='idxcase38a')
c.ev('user.session.start', at=8, actor='user38', ip='198.51.100.38', session='idxcase38b')

c = case('app-sign-on-policy-updated', ['Okta Application Sign-On Policy Modified or Deleted', MOD], 'Application sign-on policy updated')
c.ev('application.policy.sign_on.update', actor='admin39', targets=[app_target('Fixture Payroll')])

c = case('okta-support-access', ['Okta Support Access to the Org'], 'Okta Support viewed the org')
c.ev('support.org.view', actor='Okta Support', actor_type='SystemPrincipal', ip='198.51.100.40')

c = case('user-reported-suspicious', ['User Reported Suspicious Activity'], 'End user reports suspicious activity from an email notification')
c.ev('user.account.report_suspicious_activity_by_enduser', actor='user41', message='User report suspicious activity')

c = case('security-threat-detected', ['Okta Security Threat Detected'], 'ThreatInsight request from a malicious IP')
c.ev('security.threat.detected', actor='unknown', ip='203.0.113.42', severity='WARN', result='DENY',
     message='Request from suspicious actor')

c = case('protected-action', ['Okta Protected Action Attempted or Request Blocked'], 'Protected action attempted')
c.ev('security.protected_action.attempt', actor='admin43', message='Protected action attempted')

c = case('signin-after-deactivation', ['Okta Sign-In by a Recently Deactivated User'], 'Sign-in by a user deactivated 3 days earlier')
c.ev('user.lifecycle.deactivate', at=-3 * 24 * 60 - 25, actor='admin44', targets=[user_target('leaver44')])
c.ev('user.session.start', actor='leaver44', ip='203.0.113.44')

c = case('signin-after-reactivation', [], 'Deactivated 3 days earlier, re-activated 2 days earlier, then signs in: not suspicious')
c.ev('user.lifecycle.deactivate', at=-3 * 24 * 60 - 25, actor='admin45', targets=[user_target('mover45')])
c.ev('user.lifecycle.activate', at=-2 * 24 * 60 - 25, actor='admin45', targets=[user_target('mover45')])
c.ev('user.session.start', actor='mover45', ip='192.0.2.45')

c = case('account-locked', ['Locked Out or Account Locked'], 'Account locked after too many attempts, and one that reached the lockout limit')
c.ev('user.account.lock', actor='user46', result='FAILURE', severity='WARN')
c.ev('user.account.lock.limit', at=4, actor='user46b', result='FAILURE', severity='WARN')

c = case('mfa-bypass-attempt', ['Attempted Bypass of Okta MFA', MOD], 'Attempt to bypass a factor')
c.ev('user.mfa.attempt_bypass', actor='user47', result='FAILURE')

c = case('password-in-username', ['Potential Okta Password in AlternateID Field'], 'Failed sign-in where the username field holds a password-like string')
c.ev('user.session.start', actor='!Fixture-Not-A-Real-Password-48', result='FAILURE', reason='VERIFICATION_ERROR')

c = case('idp-created', ['Okta Identity Provider Created', MOD], 'Identity provider created')
c.ev('system.idp.lifecycle.create', actor='admin49', targets=[tgt('IdentityProvider', '0oafixtureidp49', None, 'Fixture IdP')])

c = case('session-impersonation', ['Okta User Session Impersonation'], 'Impersonation session started')
c.ev('user.session.impersonation.initiate', actor='admin50', targets=[user_target('user50')])

c = case('refresh-token-reuse', ['Okta OAuth Refresh Token Reuse Detected'], 'Refresh token reuse on the org and on a custom authorization server')
c.ev('app.oauth2.token.detect_reuse', actor='user51', result='FAILURE', severity='WARN')
c.ev('app.oauth2.as.token.detect_reuse', at=4, actor='user51b', result='FAILURE', severity='WARN')

c = case('signin-new-ip-after-mfa-reset', ['Okta Sign-In from a New IP After MFA Reset'],
         'Admin resets a user\'s factors from one IP; 2 hours later the user signs in from another IP')
c.ev('user.mfa.factor.reset_all', at=-2 * 60 - 25, actor='admin52', ip='192.0.2.52', targets=[user_target('user52')])
c.ev('user.session.start', actor='user52', ip='203.0.113.52')

c = case('signin-same-ip-after-own-mfa-reset', [], 'User resets their own factors and signs in from the same IP: not suspicious')
c.ev('user.mfa.factor.reset_all', at=-2 * 60 - 25, actor='user53', ip='192.0.2.53', targets=[user_target('user53')])
c.ev('user.session.start', actor='user53', ip='192.0.2.53')

c = case('password-reset-volume', ['High Number of Okta Password Reset or Unlock Events for One User'], '3 password reset / unlock events for one user')
c.ev('system.email.password_reset.sent_message', at=2, actor='user54', targets=[user_target('user54')])
c.ev('user.account.reset_password', at=4, actor='user54', targets=[user_target('user54')])
c.ev('user.account.unlock_token', at=6, actor='user54', targets=[user_target('user54')])

c = case('application-updated', ['Okta Application Modified, Deactivated or Deleted'], 'Application updated')
c.ev('application.lifecycle.update', actor='admin55', targets=[app_target('Fixture Payroll')])

c = case('session-used-from-two-countries', ['Okta Session Used from Multiple Countries'],
         'One browser session (rootSessionId) used from the United States and Brazil in the window')
c.ev('user.session.start', at=2, actor='user56', ip='192.0.2.56', session='idxcase56', root_session='idxcase56')
c.ev('user.authentication.sso', at=9, actor='user56', ip='203.0.113.56', country='Brazil', session='idxcase56',
     root_session='idxcase56', targets=[app_target('Fixture Wiki')])

c = case('mobile-session-two-networks', [], 'Same, but from a phone (Okta Verify on cellular roams across countries): ignored')
c.ev('user.authentication.auth_via_mfa', at=2, actor='user57', ip='192.0.2.57', device='Mobile', session='idxcase57')
c.ev('user.authentication.auth_via_mfa', at=9, actor='user57', ip='203.0.113.57', country='Brazil', device='Mobile',
     session='idxcase57')

c = case('policy-rule-updated', ['Okta Policy Rule Modified, Deactivated or Deleted', MOD], 'Policy rule updated')
c.ev('policy.rule.update', actor='admin58', targets=[tgt('PolicyRule', '0prfixture58', None, 'Fixture Rule')])

# ---------------------------------------------------------------------------------------------
# build / ingest
# ---------------------------------------------------------------------------------------------


def build():
    lines = sorted((json.loads(l)['published'], l) for c in CASES for l in c.events)
    with open(FIXTURES, 'w') as f:
        for _, l in lines:
            f.write(l + '\n')
    print(f'wrote {len(lines)} events for {len(CASES)} cases to {FIXTURES}')


def env():
    try:
        return os.environ['GRAVWELL_URL'].rstrip('/'), os.environ['GRAVWELL_TOKEN']
    except KeyError:
        sys.exit('set GRAVWELL_URL and GRAVWELL_TOKEN')


def ingest():
    url, token = env()
    records = []
    for l in open(FIXTURES):
        l = l.rstrip('\n')
        e = json.loads(l)
        records.append(json.dumps({'TS': e['published'], 'Tag': TAG, 'SRC': e['client']['ipAddress'],
                                   'Data': b64encode(l.encode()).decode(), 'Enumerated': None}))
    body, boundary = [], 'fixtureboundary'
    for k, v in (('type', 'reimport'), ('tag', ''), ('source', '')):
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n')
    body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="fixtures.json"\r\n'
                f'Content-Type: application/json\r\n\r\n' + '\n'.join(records) + f'\r\n--{boundary}--\r\n')
    req = urllib.request.Request(url + '/api/ingest/lines', data=''.join(body).encode(), method='POST', headers={
        'Gravwell-Token': token, 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    print(urllib.request.urlopen(req).read().decode())


# ---------------------------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------------------------


def retarget(query):
    """Point the config macro $OKTA (System Log tag) at the fixture tag; $OKTA_USERS is left alone."""
    return re.sub(r'\$OKTA\b', TAG, query)


def detections():
    out = []
    for m in glob.glob(os.path.join(KIT, 'scheduled', '*.meta')):
        meta = json.load(open(m))
        ref = meta.get('SearchReference')
        if not ref:
            continue
        # never run a query that writes a resource (the user aggregates builder ends in `table -save`)
        if re.search(r'\btable\s+-save\b', open(os.path.join(KIT, 'searchlibrary', ref + '.query')).read()):
            continue
        name = json.load(open(os.path.join(KIT, 'searchlibrary', ref + '.meta')))['Name']
        short = name.split(' - ', 2)[2]
        out.append((short, open(os.path.join(KIT, 'searchlibrary', ref + '.query')).read()))
    return sorted(out)


def compound_prefix_end(q):
    """Index just past the leading `@name{...};` blocks of a compound query (0 if there are none).

    Braces are matched, skipping quoted strings and `//` comments, because the detections' own eval code
    contains `};` too, so the last `};` in the text is not necessarily the end of the inner queries."""
    pos = 0
    while True:
        m = re.match(r'\s*@[A-Za-z0-9_]+\{', q[pos:])
        if not m:
            return pos
        i, depth, quote = pos + m.end(), 1, None
        while depth and i < len(q):
            ch = q[i]
            if quote:
                if ch == '\\':
                    i += 1
                elif ch == quote:
                    quote = None
            elif ch == '"':
                quote = ch
            elif q.startswith('//', i):
                i = q.find('\n', i)
                if i < 0:
                    break
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            i += 1
        semi = re.match(r'\s*;', q[i:])
        pos = i + (semi.end() if semi else 0)


def run(url, token, query, start, end):
    """Run a (compound) query over [start, end). Returns (rows as dicts, error)."""
    window = f'start="{start}" end="{end}" '
    q = query
    # compound queries: inner queries without their own start= get the window; the main query always does
    q = re.sub(r'(@[A-Za-z0-9_]+\{)(?!\s*start=)', lambda m: m.group(1) + window, q)
    i = compound_prefix_end(q)
    q = q[:i] + ' ' + window + q[i:].lstrip()
    # The query goes in the JSON body, not a header: detections carry `//` line comments (which would swallow the
    # rest of a query flattened onto one header line) and non-Latin-1 characters. The inline start=/end= window wins.
    req = urllib.request.Request(url + '/api/search/direct', method='POST',
                                 data=json.dumps({'SearchString': q, 'Format': 'csv'}).encode(),
                                 headers={'Gravwell-Token': token, 'Content-Type': 'application/json'})
    try:
        body = urllib.request.urlopen(req, timeout=300).read().decode()
    except urllib.error.HTTPError as e:
        return None, e.read()[:300].decode(errors='replace')
    rows = list(csv.reader(io.StringIO(body)))
    return ([dict(zip(rows[0], r)) for r in rows[1:]] if rows else []), None


def case_at(published):
    """The case whose window contains this timestamp, or None."""
    t = datetime.strptime(published[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    i, rem = divmod(t - FIXTURE_DAY, timedelta(hours=1))
    return CASES[i] if 0 <= i < len(CASES) and rem < WINDOW else None


def check(selected, jobs, full):
    """Pass 1 (unless --full): every detection once over the whole fixture span; rows are mapped to cases by
    their `published` time. Pass 2: every (case, detection) pair that fired in pass 1 or is expected, plus
    every pair for detections whose output has no `published` column, on the exact 15-minute case window.
    --full runs pass 2 on every pair (cases x detections; slow, roughly 8 s per query on a small instance)."""
    url, token = env()
    dets = dict((n, retarget(re.sub(r'/\*.*?\*/', ' ', q, flags=re.S))) for n, q in detections())
    cases = [c for c in CASES if not selected or c.name in selected]
    for c in cases:
        for e in c.expect:
            if e not in dets:
                sys.exit(f'{c.name}: expects unknown detection {e!r}')
    fmt = lambda t: t.strftime('%Y-%m-%dT%H:%M:%SZ')
    errors = []
    pool = cf.ThreadPoolExecutor(jobs)

    pairs = {(c.name, e) for c in cases for e in c.expect}
    if full:
        pairs |= {(c.name, n) for c in cases for n in dets}
    else:
        span = (fmt(min(c.start for c in cases)), fmt(max(c.start for c in cases) + WINDOW))
        names = {c.name for c in cases}
        for n, (rows, err) in zip(dets, pool.map(lambda n: run(url, token, dets[n], *span), dets)):
            if err:
                errors.append(('(span)', n, err))
            elif rows and 'published' not in rows[0]:
                pairs |= {(c.name, n) for c in cases}
            else:
                pairs |= {(c.name, n) for c in map(case_at, (r['published'] for r in rows or []))
                          if c and c.name in names}
        print(f'pass 1: {len(dets)} detections over the fixture span; pass 2: {len(pairs)} case windows')

    by_name = {c.name: c for c in CASES}

    def one(pair):
        c = by_name[pair[0]]
        return pair, run(url, token, dets[pair[1]], fmt(c.start), fmt(c.start + WINDOW))

    fired = {}
    for (cname, n), (rows, err) in pool.map(one, sorted(pairs)):
        if err:
            errors.append((cname, n, err))
        elif rows:
            fired.setdefault(cname, {})[n] = len(rows)
    covered, failures = set(), 0
    for c in cases:
        got = fired.get(c.name, {})
        missing = [e for e in c.expect if e not in got]
        extra = [n for n in got if n not in c.expect]
        covered.update(n for n in got if n in c.expect)
        failures += bool(missing or extra)
        detail = ', '.join(f'{n} ({got[n]})' for n in sorted(got)) or 'nothing'
        print(f'{"FAIL" if missing or extra else "PASS"}  {c.name:40s} fired: {detail}')
        for e in missing:
            print(f'      missing: {e}')
        for e in extra:
            print(f'      unexpected: {e}')
    for cname, n, err in errors:
        print(f'ERROR {cname} / {n}: {err}')
    if not selected:
        for n in sorted(set(dets) - covered):
            print(f'NOTE  no case covers: {n}')
    print(f'{len(cases) - failures}/{len(cases)} cases pass, {len(errors)} query errors, '
          f'{len(covered)}/{len(dets)} detections covered')
    return 1 if failures or errors else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('command', choices=['build', 'ingest', 'check', 'list'])
    p.add_argument('cases', nargs='*')
    p.add_argument('-j', '--jobs', type=int, default=6)
    p.add_argument('--full', action='store_true', help='check every case window against every detection (slow)')
    a = p.parse_args()
    if a.command == 'build':
        build()
    elif a.command == 'ingest':
        ingest()
    elif a.command == 'list':
        for c in CASES:
            print(f'{c.start:%Y-%m-%dT%H:%MZ}  {c.name:40s} {c.doc}')
    else:
        sys.exit(check(set(a.cases), a.jobs, a.full))


if __name__ == '__main__':
    main()
