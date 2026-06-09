"""modules/ip_probe.py — IP / Domain OSINT (GeoIP, WHOIS, DNS, Threat Intel)"""
import asyncio
import aiohttp
import socket
import json
import re
from rich.console import Console

console = Console()

class IPProbe:
    def __init__(self, cfg, db):
        self.cfg     = cfg
        self.db      = db
        self.timeout = aiohttp.ClientTimeout(total=cfg.timeout)

    async def scan(self, target: str) -> dict:
        is_domain = not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target)
        ip        = await self._resolve(target) if is_domain else target

        tasks = [
            self._geoip(ip),
            self._rdap(ip, is_domain, target),
            self._dns(target) if is_domain else asyncio.sleep(0),
            self._threat_intel(ip),
            self._reverse_dns(ip),
            self._shodan_free(ip),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        geo       = results[0] if not isinstance(results[0], Exception) else {}
        rdap      = results[1] if not isinstance(results[1], Exception) else {}
        dns       = results[2] if not isinstance(results[2], Exception) else {}
        threat    = results[3] if not isinstance(results[3], Exception) else {}
        reverse   = results[4] if not isinstance(results[4], Exception) else {}
        shodan    = results[5] if not isinstance(results[5], Exception) else {}

        output = {
            "scan_type":   "ip",
            "target":      target,
            "resolved_ip": ip,
            "found_count": 1,
            "data": {
                "Geolocation":     geo,
                "WHOIS / RDAP":    rdap,
                "DNS Records":     dns or {},
                "Threat Intel":    threat,
                "Reverse DNS":     reverse,
                "Shodan (free)":   shodan,
            },
        }
        self.db.save_scan("ip", target, output)
        return output

    async def _resolve(self, domain: str) -> str:
        try:
            return socket.gethostbyname(domain)
        except Exception:
            return domain

    async def _geoip(self, ip: str) -> dict:
        token = self.cfg.ipinfo_key
        url   = f"https://ipinfo.io/{ip}/json" + (f"?token={token}" if token else "")
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            async with s.get(url, ssl=False) as r:
                data = await r.json()
        return {
            "ip":          data.get("ip"),
            "hostname":    data.get("hostname"),
            "city":        data.get("city"),
            "region":      data.get("region"),
            "country":     data.get("country"),
            "coordinates": data.get("loc"),
            "org":         data.get("org"),
            "postal":      data.get("postal"),
            "timezone":    data.get("timezone"),
        }

    async def _rdap(self, ip: str, is_domain: bool, original: str) -> dict:
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            if is_domain:
                tld = original.split(".")[-1]
                url = f"https://rdap.org/domain/{original}"
            else:
                url = f"https://rdap.org/ip/{ip}"
            async with s.get(url, ssl=False) as r:
                if r.status != 200:
                    return {}
                data = await r.json()

        result = {}
        if is_domain:
            result["registrar"]     = self._rdap_val(data, ["entities","0","vcardArray","1"])
            result["registered"]    = data.get("events", [{}])[0].get("eventDate","")
            result["expires"]       = next((e.get("eventDate") for e in data.get("events",[]) if e.get("eventAction")=="expiration"), "")
            result["name_servers"]  = ", ".join(data.get("nameservers", [{}]))
            result["status"]        = ", ".join(data.get("status", []))
        else:
            result["network_name"]  = data.get("name","")
            result["handle"]        = data.get("handle","")
            result["start_address"] = data.get("startAddress","")
            result["end_address"]   = data.get("endAddress","")
            result["country"]       = data.get("country","")
            result["type"]          = data.get("type","")
        return result

    def _rdap_val(self, data, path):
        try:
            v = data
            for k in path:
                v = v[k] if isinstance(v, (dict,list)) else v
            return str(v)
        except Exception:
            return ""

    async def _dns(self, domain: str) -> dict:
        records = {}
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            for rtype in ["A","AAAA","MX","NS","TXT","CNAME","SOA"]:
                try:
                    url = f"https://dns.google/resolve?name={domain}&type={rtype}"
                    async with s.get(url, ssl=False) as r:
                        data = await r.json()
                    answers = data.get("Answer", [])
                    if answers:
                        records[rtype] = [a.get("data","") for a in answers]
                except Exception:
                    pass
        return records

    async def _threat_intel(self, ip: str) -> dict:
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            try:
                url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}"
                async with s.get(url, headers={"Key": "free", "Accept": "application/json"}, ssl=False) as r:
                    data = (await r.json()).get("data", {})
                return {
                    "abuse_score":     data.get("abuseConfidenceScore", 0),
                    "is_whitelisted":  data.get("isWhitelisted", False),
                    "total_reports":   data.get("totalReports", 0),
                    "last_reported":   data.get("lastReportedAt", ""),
                    "isp":             data.get("isp",""),
                    "usage_type":      data.get("usageType",""),
                    "is_tor":          data.get("isTor", False),
                }
            except Exception:
                return {"note": "AbuseIPDB free key needed for full threat data"}

    async def _reverse_dns(self, ip: str) -> dict:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return {"reverse_hostname": hostname}
        except Exception:
            return {"reverse_hostname": "N/A"}

    async def _shodan_free(self, ip: str) -> dict:
        async with aiohttp.ClientSession(timeout=self.timeout) as s:
            try:
                url = f"https://internetdb.shodan.io/{ip}"
                async with s.get(url, ssl=False) as r:
                    if r.status != 200:
                        return {}
                    data = await r.json()
                return {
                    "open_ports":  ", ".join(str(p) for p in data.get("ports", [])),
                    "cpes":        ", ".join(data.get("cpes", [])),
                    "hostnames":   ", ".join(data.get("hostnames", [])),
                    "tags":        ", ".join(data.get("tags", [])),
                    "vulns":       ", ".join(data.get("vulns", [])),
                }
            except Exception:
                return {}
