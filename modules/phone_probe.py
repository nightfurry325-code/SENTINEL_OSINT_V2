"""modules/phone_probe.py — Phone number intelligence"""
import re
import requests
from rich.console import Console

console = Console()

COUNTRY_CODES = {
    "+1":"United States / Canada","+7":"Russia / Kazakhstan","+20":"Egypt","+27":"South Africa",
    "+30":"Greece","+31":"Netherlands","+32":"Belgium","+33":"France","+34":"Spain",
    "+36":"Hungary","+39":"Italy","+40":"Romania","+41":"Switzerland","+43":"Austria",
    "+44":"United Kingdom","+45":"Denmark","+46":"Sweden","+47":"Norway","+48":"Poland",
    "+49":"Germany","+51":"Peru","+52":"Mexico","+53":"Cuba","+54":"Argentina",
    "+55":"Brazil","+56":"Chile","+57":"Colombia","+58":"Venezuela","+60":"Malaysia",
    "+61":"Australia","+62":"Indonesia","+63":"Philippines","+64":"New Zealand",
    "+65":"Singapore","+66":"Thailand","+81":"Japan","+82":"South Korea",
    "+84":"Vietnam","+86":"China","+90":"Turkey","+91":"India","+92":"Pakistan",
    "+93":"Afghanistan","+94":"Sri Lanka","+95":"Myanmar","+98":"Iran",
    "+212":"Morocco","+213":"Algeria","+216":"Tunisia","+218":"Libya",
    "+220":"Gambia","+221":"Senegal","+234":"Nigeria","+254":"Kenya",
    "+255":"Tanzania","+256":"Uganda","+260":"Zambia","+263":"Zimbabwe",
    "+380":"Ukraine","+381":"Serbia","+385":"Croatia","+386":"Slovenia",
    "+420":"Czech Republic","+421":"Slovakia","+852":"Hong Kong",
    "+853":"Macau","+855":"Cambodia","+856":"Laos","+880":"Bangladesh",
    "+886":"Taiwan","+960":"Maldives","+966":"Saudi Arabia","+971":"UAE",
    "+972":"Israel","+974":"Qatar","+977":"Nepal","+992":"Tajikistan",
    "+993":"Turkmenistan","+994":"Azerbaijan","+995":"Georgia","+996":"Kyrgyzstan",
    "+998":"Uzbekistan",
}

CARRIER_PATTERNS = {
    "Indonesia": {
        "Telkomsel":   ["+6281[0-9]", "+6282[0-9]", "+6285[3-8]"],
        "Indosat":     ["+6283[0-8]", "+6285[6-8]", "+6286[0-9]"],
        "XL Axiata":   ["+6287[0-9]", "+6285[9]",   "+6889"],
        "Smartfren":   ["+6288[0-9]"],
        "Tri (3)":     ["+6289[0-9]"],
        "Axis":        ["+6283[7-8]"],
    },
    "United States": {
        "AT&T":        ["+1[2-9][0-9]{2}[2-9][0-9]{6}"],
        "Verizon":     ["+1[2-9][0-9]{2}[2-9][0-9]{6}"],
        "T-Mobile":    ["+1[2-9][0-9]{2}[2-9][0-9]{6}"],
    },
}

class PhoneProbe:
    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db  = db

    def scan(self, phone: str) -> dict:
        data = {}
        data["raw_number"]   = phone
        data["e164_format"]  = phone
        data["country"]      = self._detect_country(phone)
        data["region_code"]  = self._extract_code(phone)
        data["carrier"]      = self._detect_carrier(phone, data["country"])
        data["line_type"]    = self._detect_line_type(phone)
        data["valid_format"] = self._validate_format(phone)
        data["local_format"] = self._to_local(phone)
        data["possible_spam"]= self._check_spam_indicators(phone)

        # Optional: NumVerify API
        if self.cfg.numverify_key:
            api_data = self._numverify(phone)
            if api_data:
                data.update(api_data)

        result = {
            "scan_type":   "phone",
            "target":      phone,
            "found_count": 1,
            "data":        data,
        }
        self.db.save_scan("phone", phone, result)
        return result

    def _extract_code(self, phone):
        for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
            if phone.startswith(code):
                return code
        return "unknown"

    def _detect_country(self, phone):
        code = self._extract_code(phone)
        return COUNTRY_CODES.get(code, "Unknown")

    def _detect_carrier(self, phone, country):
        patterns = CARRIER_PATTERNS.get(country, {})
        for carrier, pats in patterns.items():
            for pat in pats:
                if re.match(pat, phone):
                    return carrier
        return "Unknown"

    def _detect_line_type(self, phone):
        # Heuristic based on number patterns
        if re.match(r"\+1[89]00", phone):
            return "Toll-Free"
        if re.match(r"\+1900", phone):
            return "Premium"
        if len(phone) < 8:
            return "Short Code"
        return "Mobile / Landline"

    def _validate_format(self, phone):
        cleaned = re.sub(r"[^\d+]", "", phone)
        if not cleaned.startswith("+"):
            return "❌ Missing country code"
        if len(cleaned) < 7 or len(cleaned) > 16:
            return "❌ Invalid length"
        return "✅ Valid E.164"

    def _to_local(self, phone):
        code = self._extract_code(phone)
        if code != "unknown":
            return "0" + phone[len(code):]
        return phone

    def _check_spam_indicators(self, phone):
        # Simple heuristic
        if re.match(r"\+1(800|888|877|866|855|844|833|822)", phone):
            return "⚠ Possible marketing/spam"
        return "✅ No indicators"

    def _numverify(self, phone):
        try:
            r = requests.get(
                "http://apilayer.net/api/validate",
                params={"access_key": self.cfg.numverify_key, "number": phone, "format": 1},
                timeout=self.cfg.timeout,
            )
            d = r.json()
            return {
                "valid":         d.get("valid"),
                "country_name":  d.get("country_name"),
                "carrier":       d.get("carrier"),
                "line_type_api": d.get("line_type"),
                "location":      d.get("location"),
            }
        except Exception:
            return None
