import ipaddress
import re
import urllib.request
from bs4 import BeautifulSoup
import socket
import requests
from googlesearch import search
import whois
from datetime import date
from urllib.parse import urlparse, urljoin


class FeatureExtraction:

    def __init__(self, url):
        self.url = url
        self.domain = ""
        self.whois_response = None
        self.urlparse = None
        self.response = None
        self.soup = None
        self.features = []
        try:
            self.response = requests.get(url, timeout=5)
            self.soup = BeautifulSoup(self.response.text, "html.parser")
        except:
            pass
        try:
            self.urlparse = urlparse(url)
            self.domain = self.urlparse.netloc
        except:
            pass
        try:
            self.whois_response = whois.whois(self.domain)
        except:
            pass
        # Extract all features
        self.features = [
            self.UsingIp(),
            self.longUrl(),
            self.shortUrl(),
            self.symbol(),
            self.redirecting(),
            self.prefixSuffix(),
            self.SubDomains(),
            self.Https(),
            self.DomainRegLen(),
            self.Favicon(),
            self.NonStdPort(),
            self.HTTPSDomainURL(),
            self.RequestURL(),
            self.AnchorURL(),
            self.LinksInScriptTags(),
            self.ServerFormHandler(),
            self.InfoEmail(),
            self.AbnormalURL(),
            self.WebsiteForwarding(),
            self.StatusBarCust(),
            self.DisableRightClick(),
            self.UsingPopupWindow(),
            self.IframeRedirection(),
            self.AgeofDomain(),
            self.DNSRecording(),
            self.WebsiteTraffic(),
            self.PageRank(),
            self.GoogleIndex(),
            self.LinksPointingToPage(),
            self.StatsReport(),
        ]
    # 1. Using IP Address instead of domain
    def UsingIp(self):
        try:
            ipaddress.ip_address(self.url)
            return -1
        except:
            return 1
    # 2. Length of URL
    def longUrl(self):
        if len(self.url) < 54:
            return 1
        elif 54 <= len(self.url) <= 75:
            return 0
        return -1
    # 3. Shortened URL
    def shortUrl(self):
        shorteners = (
            "bit.ly|goo.gl|shorte.st|x.co|ow.ly|t.co|tinyurl|"
            "adf.ly|is.gd|cutt.us|po.st|bc.vc|u.to|j.mp|qr.net|v.gd|tr.im"
        )
        return -1 if re.search(shorteners, self.url) else 1
    # 4. @ Symbol
    def symbol(self):
        return -1 if "@" in self.url else 1
    # 5. Redirecting "//" in URL path
    def redirecting(self):
        return -1 if self.url.rfind("//") > 6 else 1
    # 6. Prefix/Suffix in domain (e.g., google-login.com)
    def prefixSuffix(self):
        return -1 if "-" in self.domain else 1
    # 7. Subdomains count
    def SubDomains(self):
        parts = self.domain.split(".")
        return 1 if len(parts) <= 2 else 0 if len(parts) == 3 else -1
    # 8. HTTPS usage
    def Https(self):
        return 1 if self.urlparse.scheme == "https" else -1
    # 9. Domain Registration Length
    def DomainRegLen(self):
        try:
            exp = self.whois_response.expiration_date
            cre = self.whois_response.creation_date
            if isinstance(exp, list): exp = exp[0]
            if isinstance(cre, list): cre = cre[0]
            age = (exp.year - cre.year) * 12 + (exp.month - cre.month)
            return 1 if age >= 12 else -1
        except:
            return -1
    # 10. Favicon check (icon hosted externally?)
    def Favicon(self):
        try:
            if not self.soup:
                return -1
            for link in self.soup.find_all("link", href=True):
                rel = link.get("rel") or []
                if any("icon" in r.lower() for r in rel):
                    href = link["href"]
                    full = urljoin(self.url, href)
                    if urlparse(full).netloc == self.domain:
                        return 1
                    else:
                        return -1
            return -1
        except:
            return -1
    # 11. Non-Standard Port
    def NonStdPort(self):
        try:
            port = self.urlparse.port
            if port is None:
                return 1
            if (self.urlparse.scheme == "https" and port == 443) or (self.urlparse.scheme == "http" and port == 80):
                return 1
            return -1
        except:
            return -1
    # 12. HTTPS in Domain Name
    def HTTPSDomainURL(self):
        return -1 if "https" in self.domain else 1
    # 13. External Request URLs (img, iframe, embed)
    def RequestURL(self):
        try:
            if not self.soup:
                return -1
            tags = self.soup.find_all(["img", "audio", "embed", "iframe"], src=True)
            total = len(tags)
            same = sum(1 for t in tags if self.domain in t["src"])
            if total == 0:
                return 0
            perc = same / total * 100
            if perc < 22:
                return 1
            elif perc < 61:
                return 0
            return -1
        except:
            return -1
    # 14. Anchor URLs (unsafe links)
    def AnchorURL(self):
        try:
            if not self.soup:
                return -1
            anchors = self.soup.find_all("a", href=True)
            total = len(anchors)
            unsafe = 0
            for a in anchors:
                href = a["href"]
                if (
                    "#" in href
                    or "javascript" in href.lower()
                    or "mailto" in href.lower()
                    or self.domain not in href
                ):
                    unsafe += 1
            if total == 0:
                return -1
            perc = (unsafe / total) * 100
            if perc < 31:
                return 1
            elif perc < 67:
                return 0
            return -1
        except:
            return -1
    # 15. Links in <script> or <link>
    def LinksInScriptTags(self):
        try:
            if not self.soup:
                return -1
            tags = self.soup.find_all(["link", "script"])
            total = len(tags)
            same = sum(
                1
                for t in tags
                if (t.get("href") and self.domain in t["href"])
                or (t.get("src") and self.domain in t["src"])
            )
            if total == 0:
                return 0
            perc = same / total * 100
            if perc > 81:
                return 1
            elif perc > 17:
                return 0
            return -1
        except:
            return -1
    # 16. Form handler action attribute
    def ServerFormHandler(self):
        try:
            forms = self.soup.find_all("form", action=True)
            if not forms:
                return 1
            for form in forms:
                action = form["action"]
                if action in ("", "about:blank"):
                    return -1
                elif self.domain not in action:
                    return 0
            return 1
        except:
            return -1
    # 17. InfoEmail presence
    def InfoEmail(self):
        try:
            return -1 if re.findall(r"[mail\(\)|mailto:?]", str(self.soup)) else 1
        except:
            return -1
    # 18. Abnormal URL behavior
    def AbnormalURL(self):
        try:
            return 1 if self.domain in self.response.text else -1
        except:
            return -1
    # 19. Website Forwarding count
    def WebsiteForwarding(self):
        try:
            h = len(self.response.history)
            if h <= 1:
                return 1
            elif h <= 4:
                return 0
            return -1
        except:
            return -1
    # 20. Status Bar Customization (onmouseover)
    def StatusBarCust(self):
        try:
            return -1 if re.search("onmouseover", self.response.text, re.I) else 1
        except:
            return -1
    # 21. Disable Right Click
    def DisableRightClick(self):
        try:
            return -1 if re.search(r"event.button ?== ?2", self.response.text) else 1
        except:
            return -1
    # 22. Popup Windows
    def UsingPopupWindow(self):
        try:
            return -1 if re.search(r"alert\(", self.response.text) else 1
        except:
            return -1
    # 23. Iframe Redirection
    def IframeRedirection(self):
        try:
            return -1 if re.search(r"<iframe", self.response.text, re.I) else 1
        except:
            return -1
    # 24. Domain Age
    def AgeofDomain(self):
        try:
            creation = self.whois_response.creation_date
            if isinstance(creation, list):
                creation = creation[0]
            today = date.today()
            age = (today.year - creation.year) * 12 + (today.month - creation.month)
            return 1 if age >= 6 else -1
        except:
            return -1
    # 25. DNS Recording
    def DNSRecording(self):
        return self.AgeofDomain()
    # 26. Website Traffic (Alexa rank)
    def WebsiteTraffic(self):
        try:
            xml = urllib.request.urlopen(f"http://data.alexa.com/data?cli=10&dat=s&url={self.url}").read()
            rank = BeautifulSoup(xml, "xml").find("REACH")["RANK"]
            return 1 if int(rank) < 100000 else 0
        except:
            return -1
    # 27. PageRank (from external service)
    def PageRank(self):
        try:
            resp = requests.post("https://www.checkpagerank.net/index.php", data={"name": self.domain}, timeout=5)
            m = re.search(r"Global Rank:\s*([0-9,]+)", resp.text)
            if not m:
                return -1
            rank = int(m.group(1).replace(",", ""))
            return 1 if rank < 100000 else -1
        except:
            return -1
    # 28. Google Index check
    def GoogleIndex(self):
        try:
            result = search(self.url, 1)
            return 1 if result else -1
        except:
            return 1
    # 29. Links pointing to page
    def LinksPointingToPage(self):
        try:
            links = len(re.findall(r"<a href=", self.response.text))
            if links == 0:
                return 1
            elif links <= 2:
                return 0
            return -1
        except:
            return -1
    # 30. Stats Report (blacklisted domains/IPs)
    def StatsReport(self):
        try:
            bad_hosts = ["at.ua", "usa.cc", "ow.ly", "pe.hu", "hol.es", "96.lt"]
            for bad in bad_hosts:
                if bad in self.domain:
                    return -1
            ip = socket.gethostbyname(self.domain)
            bad_ips = ["146.112.61.108", "213.174.157.151", "121.50.168.88"]
            return -1 if ip in bad_ips else 1
        except:
            return 1
    def getFeaturesList(self):
        return self.features
