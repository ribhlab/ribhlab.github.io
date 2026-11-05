"""OIDC-restricted ProfitLens Team package bridge. Digital files never placed in public GitHub."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import hashlib, io, os
import jwt, requests
from jwt import PyJWKClient
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pypdf import PdfReader

ISSUER="https://token.actions.githubusercontent.com"
AUDIENCE="ribhlab-profitlens-team-v36-transfer"
REPO="ribhlab/ribhlab.github.io"
WORKFLOW_REF=REPO+"/.github/workflows/etsy-profitlens-team-v36-publish.yml@refs/heads/main"
SOURCE="https://ribhlab.wordpress.com/wp-content/uploads/2026/11/profitlens-team-v36-encrypted-transfer.pdf"
PDF_SHA="728b376379f5bfa33e8633966da2c735047dbfa0bd2cd5c6a175cf638af98b4c"
ZIP_SHA="c19d9e8eee24b2a0640ef8b45d73404796df7062524cd650651497d7d0a38f54"
AAD=b"ribhlab-profitlens-team-v36-etsy-v1"
JWK=PyJWKClient(ISSUER+"/.well-known/jwks",cache_jwk_set=True,lifespan=300)

class handler(BaseHTTPRequestHandler):
 def _reply(self,status,body=b"",content_type="text/plain; charset=utf-8"):
  self.send_response(status)
  self.send_header("Content-Type",content_type)
  self.send_header("Content-Length",str(len(body)))
  self.send_header("Cache-Control","private, no-store")
  self.send_header("X-Content-Type-Options","nosniff")
  self.send_header("Referrer-Policy","no-referrer")
  self.end_headers()
  if body:self.wfile.write(body)
 def do_GET(self):
  if urlparse(self.path).path not in ("/api/package","/package"):
   return self._reply(404,b"not_found")
  auth=self.headers.get("Authorization","")
  if not auth.startswith("Bearer ") or not 200<=len(auth)<=18015:
   return self._reply(401,b"missing_oidc_token")
  try:
   token=auth.removeprefix("Bearer ")
   signing_key=JWK.get_signing_key_from_jwt(token).key
   claims=jwt.decode(token,signing_key,algorithms=["RS256"],issuer=ISSUER,audience=AUDIENCE,leeway=10,options={"require":["iss","aud","exp","iat","sub"]})
  except Exception:
   return self._reply(403,b"oidc_signature_or_audience_rejected")
  allowed=(claims.get("repository")==REPO
           and claims.get("ref")=="refs/heads/main"
           and claims.get("workflow_ref")==WORKFLOW_REF
           and claims.get("event_name") in ("push","workflow_dispatch"))
  if not allowed:
   return self._reply(403,b"oidc_repository_or_workflow_rejected")
  try:
   key=bytes.fromhex(os.environ["TEAM_ZIP_KEY_HEX"].strip())
   if len(key)!=32:raise ValueError("bad key")
   r=requests.get(SOURCE,timeout=50)
   if not r.ok:return self._reply(502,b"encrypted_pdf_unavailable")
   if hashlib.sha256(r.content).hexdigest()!=PDF_SHA:return self._reply(502,b"encrypted_pdf_hash_mismatch")
   pdf=PdfReader(io.BytesIO(r.content))
   item=pdf.attachments.get("profitlens-team-v36.enc")
   sealed=item[0] if isinstance(item,list) else item
   if not sealed or sealed[:8]!=b"RIBHTEAM":return self._reply(502,b"encrypted_attachment_invalid")
   payload=AESGCM(key).decrypt(sealed[8:20],sealed[20:],AAD)
   if hashlib.sha256(payload).hexdigest()!=ZIP_SHA:return self._reply(502,b"buyer_package_hash_mismatch")
   return self._reply(200,payload,"application/zip")
  except Exception:
   return self._reply(502,b"secure_transfer_unavailable")
