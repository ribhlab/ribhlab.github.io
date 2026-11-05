from http.server import BaseHTTPRequestHandler
import hashlib,io,os
import jwt,requests
from jwt import PyJWKClient
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pypdf import PdfReader
ISSUER="https://token.actions.githubusercontent.com"
AUDIENCE="ribhlab-profitlens-team-v36-transfer"
REPO="ribhlab/ribhlab.github.io"
WORKFLOW=REPO+"/.github/workflows/etsy-profitlens-team-v36-publish.yml@refs/heads/main"
SUBJECT="repo:ribhlab@349031564/ribhlab.github.io@1436299009:ref:refs/heads/main"
PDF_URL="https://ribhlab.wordpress.com/wp-content/uploads/2026/11/profitlens-team-v36-encrypted-transfer.pdf"
PDF_SHA="728b376379f5bfa33e8633966da2c735047dbfa0bd2cd5c6a175cf638af98b4c"
ZIP_SHA="c19d9e8eee24b2a0640ef8b45d73404796df7062524cd650651497d7d0a38f54"
JWKS=PyJWKClient(ISSUER+"/.well-known/jwks")
class handler(BaseHTTPRequestHandler):
 def fail(self,code):
  self.send_response(code);self.send_header("Cache-Control","no-store, private");self.send_header("X-Content-Type-Options","nosniff");self.end_headers()
 def do_GET(self):
  auth=self.headers.get("Authorization","")
  if not auth.startswith("Bearer ") or len(auth)>18010:return self.fail(401)
  token=auth[7:]
  try:
   key=JWKS.get_signing_key_from_jwt(token).key
   c=jwt.decode(token,key,algorithms=["RS256"],issuer=ISSUER,audience=AUDIENCE,leeway=5)
   if c.get("repository")!=REPO or c.get("ref")!="refs/heads/main" or c.get("workflow_ref")!=WORKFLOW or c.get("sub")!=SUBJECT or c.get("event_name") not in ("push","workflow_dispatch"):return self.fail(403)
  except Exception:return self.fail(401)
  try:
   r=requests.get(PDF_URL,timeout=45)
   if not r.ok or len(r.content)>7*1024*1024 or hashlib.sha256(r.content).hexdigest()!=PDF_SHA:raise ValueError("archive")
   x=PdfReader(io.BytesIO(r.content)).attachments["profitlens-team-v36.enc"]
   x=x[0] if isinstance(x,list) else x
   if not x.startswith(b"RIBHTEAM"):raise ValueError("magic")
   raw=AESGCM(bytes.fromhex(os.environ["TEAM_ZIP_KEY_HEX"])).decrypt(x[8:20],x[20:],b"ribhlab-profitlens-team-v36-etsy-v1")
   if hashlib.sha256(raw).hexdigest()!=ZIP_SHA:raise ValueError("checksum")
  except Exception:return self.fail(502)
  self.send_response(200);self.send_header("Content-Type","application/zip");self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store, private");self.end_headers();self.wfile.write(raw)
