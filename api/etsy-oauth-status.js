const ORIGIN = "https://ribhlab.github.io";
export default function handler(req,res) {
 res.setHeader("Cache-Control","no-store, private");
 res.setHeader("X-Content-Type-Options","nosniff");
 res.setHeader("Referrer-Policy","no-referrer");
 res.setHeader("Vary","Origin");
 const origin=req.headers.origin;
 if(origin && origin!==ORIGIN) return res.status(403).json({error:"origin_not_allowed"});
 if(origin===ORIGIN) res.setHeader("Access-Control-Allow-Origin",ORIGIN);
 res.setHeader("Access-Control-Allow-Methods","GET, OPTIONS");
 if(req.method==="OPTIONS") return res.status(204).end();
 if(req.method!=="GET") return res.status(405).json({error:"method_not_allowed"});
 return res.status(200).json({status:"ready",protocol:"etsy-oauth-bridge-v1"});
}
