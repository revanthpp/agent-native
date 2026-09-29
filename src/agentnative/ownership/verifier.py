from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from agentnative.ownership.models import Environment, OwnershipVerification, VerificationStatus


class OwnershipVerifier:
    def __init__(self, ttl: timedelta = timedelta(hours=24)): self.ttl = ttl
    @staticmethod
    def challenge(): return secrets.token_urlsafe(32)
    @staticmethod
    def _host(target):
        host=urlsplit(target if "://" in target else f"https://{target}").hostname
        if not host: raise ValueError("target must include a hostname")
        return host.lower().rstrip(".")
    def _result(self, business_id, target, method, challenge, environment, evidence, valid):
        now=datetime.now(timezone.utc); return OwnershipVerification(f"verify-{hashlib.sha256(f'{business_id}:{target}:{challenge}'.encode()).hexdigest()[:24]}", business_id, target, method, hashlib.sha256(challenge.encode()).hexdigest(), now, now+self.ttl, environment, VerificationStatus.VERIFIED if valid else VerificationStatus.INVALID, evidence)
    def verify_dns(self, business_id, target, challenge, lookup_txt, environment):
        host=self._host(target); return self._result(business_id,target,"DNS_TXT",challenge,environment,f"dns://{host}/TXT",f"agent-native-verification={challenge}" in (lookup_txt(host) or []))
    def verify_https(self, business_id, target, challenge, fetch, environment):
        host=self._host(target); url=f"https://{host}/.well-known/agent-native-verification"; response=fetch(url); final=getattr(response,"url",url); body=getattr(response,"text",response if isinstance(response,str) else ""); return self._result(business_id,target,"HTTPS_WELL_KNOWN",challenge,environment,url,self._host(final)==host and body.strip()==challenge)
