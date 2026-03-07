from config import (
    GDELT_API_URL, GDELT_MAX_RECORDS, GDELT_TIMESPAN_DAYS,
    NEGATIVE_KEYWORDS, INDIAN_NEWS_DOMAINS, DEBUG_MODE
)
from src.schemas import ResearchFindings, NewsItem
from typing import List
import requests
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class ResearchAgent:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (IntelliCredit Research Agent)"
        })
        print("Research Agent ready.")

    def research(self, company_name: str,
                 promoter_name: str = "") -> ResearchFindings:
        print(f"Researching: {company_name}")
        findings = ResearchFindings(company_name=company_name)

        print("  Searching news (Google News + GDELT)...")

        # BUG FIX 1 + 4: Use exact phrase + India geo-filter as base query.
        # Wrap company name in quotes so Google News treats it as an exact phrase,
        # not individual words. Append "India" to bias toward Indian results.
        # Split boolean OR queries into separate calls (Bug 4 fix) — RSS ignores OR.
        base_query = f'"{company_name}" India'
        news_items = self._search_google_news(base_query, company_name)

        # BUG FIX 4: Separate searches instead of boolean OR in one query.
        # Each call targets a specific risk signal independently.
        risk_queries = [
            f'"{company_name}" fraud',
            f'"{company_name}" GST notice',
            f'"{company_name}" GST penalty',
            f'"{company_name}" court case',
            f'"{company_name}" FIR',
            f'"{company_name}" defaulter',
            f'"{company_name}" arrest',
        ]
        positive_queries = [
            f'"{company_name}" expansion',
            f'"{company_name}" export contract',
            f'"{company_name}" award',
        ]

        for q in risk_queries:
            news_items.extend(self._search_google_news(q, company_name))
        for q in positive_queries:
            news_items.extend(self._search_google_news(q, company_name))

        # Promoter search — search for promoter name alongside company name.
        # IMPORTANT: relevance filter uses company_name tokens (not promoter tokens)
        # so results must mention the company, not just the promoter personally.
        # e.g. "Rajesh Mehta" + "Sunrise Apparels" — rejects Lilavati Hospital articles.
        if promoter_name:
            promoter_query = f'"{promoter_name}" "{company_name}"'
            news_items.extend(self._search_google_news(
                promoter_query, company_name))

        # Fallback to GDELT if Google News got nothing
        if not news_items:
            print("  Google News empty, trying GDELT...")
            news_items = self._search_gdelt(company_name, company_name)
            if promoter_name:
                # Also require company name in GDELT promoter search
                news_items.extend(self._search_gdelt(
                    f'{promoter_name} {company_name}', company_name))

        # Deduplicate by title
        seen_titles = set()
        unique_items = []
        for item in news_items:
            if item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_items.append(item)
        news_items = unique_items

        for item in news_items:
            if item.is_negative:
                findings.negative_news.append(item)
            else:
                findings.positive_news.append(item)

        total_news = len(news_items)
        neg_count = len(findings.negative_news)
        if total_news > 0:
            findings.news_risk_score = round((neg_count / total_news) * 10, 1)

        print("  Checking MCA filings...")
        findings.mca_charges = self._check_mca(company_name)

        print("  Checking e-Courts...")
        findings.litigation_details = self._check_ecourts(company_name)
        findings.litigation_found = len(findings.litigation_details) > 0

        print("  Checking RBI/SEBI...")
        findings.rbi_sebi_actions = self._check_rbi_sebi(company_name)

        findings.research_summary = self._build_summary(findings)

        print(f"  Research complete: {neg_count} negative news, "
              f"litigation={findings.litigation_found}")
        return findings

    def research_with_mock(self, company_name: str,
                           risk_level: str = "medium") -> ResearchFindings:
        findings = ResearchFindings(company_name=company_name)

        if risk_level == "low":
            findings.negative_news = []
            findings.positive_news = [
                NewsItem(
                    title=f"{company_name} wins export order worth Rs 12 Cr",
                    url="https://economictimes.com",
                    date="20240115",
                    source="economictimes.indiatimes.com",
                    is_negative=False,
                    keywords_found=[]
                ),
                NewsItem(
                    title=f"{company_name} receives ISO 9001 certification",
                    url="https://business-standard.com",
                    date="20240210",
                    source="business-standard.com",
                    is_negative=False,
                    keywords_found=[]
                )
            ]
            findings.news_risk_score = 1.0
            findings.litigation_found = False
            findings.litigation_details = []
            findings.mca_charges = []
            findings.rbi_sebi_actions = []

        elif risk_level == "high":
            findings.negative_news = [
                NewsItem(
                    title=f"{company_name} under ED investigation for fraud",
                    url="https://economictimes.com",
                    date="20240301",
                    source="economictimes.indiatimes.com",
                    is_negative=True,
                    keywords_found=["fraud", "investigation"]
                ),
                NewsItem(
                    title=f"{company_name} directors arrested in GST scam",
                    url="https://livemint.com",
                    date="20240215",
                    source="livemint.com",
                    is_negative=True,
                    keywords_found=["arrest", "scam"]
                ),
                NewsItem(
                    title=f"{company_name} declared wilful defaulter by SBI",
                    url="https://moneycontrol.com",
                    date="20240110",
                    source="moneycontrol.com",
                    is_negative=True,
                    keywords_found=["wilful defaulter", "NPA"]
                )
            ]
            findings.positive_news = []
            findings.news_risk_score = 8.5
            findings.litigation_found = True
            findings.litigation_details = [
                "Civil suit filed by HDFC Bank — Rs 2.3 Cr recovery",
                "Criminal complaint under IPC 420 — cheating",
                "GST tribunal case — disputed ITC of Rs 85 Lakhs"
            ]
            findings.mca_charges = [
                {
                    "type": "Unsatisfied Charge",
                    "source": "MCA21",
                    "details": "Charge of Rs 5 Cr in favour of Axis Bank",
                    "risk_level": "High"
                }
            ]
            findings.rbi_sebi_actions = [
                f"RBI penalty of Rs 10 Lakh imposed on {company_name} "
                f"for KYC violations — Jan 2024"
            ]

        else:
            findings.negative_news = [
                NewsItem(
                    title=f"{company_name} faces GST notice for ITC mismatch",
                    url="https://economictimes.com",
                    date="20240201",
                    source="economictimes.indiatimes.com",
                    is_negative=True,
                    keywords_found=["GST"]
                )
            ]
            findings.positive_news = [
                NewsItem(
                    title=f"{company_name} reports 15% revenue growth in Q3",
                    url="https://business-standard.com",
                    date="20240115",
                    source="business-standard.com",
                    is_negative=False,
                    keywords_found=[]
                )
            ]
            findings.news_risk_score = 3.5
            findings.litigation_found = False
            findings.litigation_details = []
            findings.mca_charges = []
            findings.rbi_sebi_actions = []

        findings.research_summary = self._build_summary(findings)
        return findings

    def _build_relevance_tokens(self, company_name: str) -> set:
        """Extract meaningful tokens from company name for relevance filtering."""
        stopwords = {"pvt", "ltd", "private", "limited", "co", "india",
                     "the", "and", "of", "for", "in", "a", "an", "inc", "llp"}
        tokens = set()
        for token in company_name.lower().split():
            clean = token.strip(".,()-&")
            if clean not in stopwords and len(clean) > 2:
                tokens.add(clean)
        return tokens

    def _is_relevant_to_company(self, title: str, relevance_tokens: set,
                                company_name: str = "") -> bool:
        """
        Check if a news article title is actually about the company.

        Strategy (in order of preference):
          1. Full company name substring present → definitely relevant
          2. ALL meaningful tokens present → likely relevant
          3. Only SOME tokens present → reject (e.g. "Rajesh" alone matches
             unrelated articles about other people named Rajesh)

        This prevents false positives like a crime article about "Rajesh Mehta"
        (Lilavati Hospital) appearing for a search on "Sunrise Apparels" whose
        promoter happens to also be named Rajesh Mehta.
        """
        if not relevance_tokens:
            return True
        title_lower = title.lower()

        # Best check: full company name present (case-insensitive substring)
        if company_name and company_name.lower() in title_lower:
            return True

        # Strong check: ALL tokens present
        if len(relevance_tokens) >= 2:
            return all(t in title_lower for t in relevance_tokens)

        # Single token: just require it to be present
        return any(t in title_lower for t in relevance_tokens)

    def _search_gdelt(self, query: str, company_name: str = "") -> List[NewsItem]:
        items = []
        relevance_tokens = self._build_relevance_tokens(company_name or query)
        try:
            params = {
                "query": f'"{query}" sourcelang:eng',
                "mode": "artlist",
                "maxrecords": GDELT_MAX_RECORDS,
                "timespan": f"{GDELT_TIMESPAN_DAYS}d",
                "format": "json",
                "sort": "datedesc"
            }
            response = self.session.get(
                GDELT_API_URL, params=params, timeout=10
            )
            if response.status_code != 200:
                return items
            data = response.json()
            for article in data.get("articles", []):
                title = article.get("title", "")
                if not title:
                    continue
                # Apply same relevance filter as Google News
                if not self._is_relevant_to_company(title, relevance_tokens, company_name):
                    if DEBUG_MODE:
                        print(f"  GDELT filtered irrelevant: {title[:60]}")
                    continue
                title_lower = title.lower()
                found_keywords = [
                    kw for kw in NEGATIVE_KEYWORDS if kw in title_lower
                ]
                items.append(NewsItem(
                    title=title,
                    url=article.get("url", ""),
                    date=article.get("seendate", "")[:8],
                    source=article.get("domain", ""),
                    is_negative=len(found_keywords) > 0,
                    keywords_found=found_keywords
                ))
        except requests.exceptions.Timeout:
            print("  GDELT timeout — skipping news search")
        except Exception as e:
            if DEBUG_MODE:
                print(f"  GDELT error: {e}")
        return items

    def _search_google_news(self, query: str,
                            company_name: str = "") -> List[NewsItem]:
        """
        Search Google News RSS for real-time news.

        BUG FIX 1: query must already have the company name in quotes
                   (caller's responsibility — see research() above).
        BUG FIX 2: INDIAN_NEWS_DOMAINS is now actually used to filter results.
        BUG FIX 3: Post-fetch relevance check — article title must contain
                   a significant word from the company name to be included.
        """
        items = []
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = (
                f"https://news.google.com/rss/search"
                f"?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            )

            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                if DEBUG_MODE:
                    print(f"  Google News returned {response.status_code}")
                return items

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, "xml")
            articles = soup.find_all("item")[:15]

            relevance_tokens = self._build_relevance_tokens(
                company_name) if company_name else set()

            for article in articles:
                title_tag = article.find("title")
                title = title_tag.text if title_tag else ""
                link_tag = article.find("link")
                link = link_tag.text if link_tag else ""
                pub_date_tag = article.find("pubDate")
                pub_date = pub_date_tag.text[:10] if pub_date_tag else ""
                source_tag = article.find("source")
                source = source_tag.text if source_tag else "Google News"

                if not title:
                    continue

                title_lower = title.lower()
                if not self._is_relevant_to_company(title, relevance_tokens, company_name):
                    if DEBUG_MODE:
                        print(f"  Filtered irrelevant: {title[:60]}")
                    continue

                # BUG FIX 2: Domain filter — INDIAN_NEWS_DOMAINS was imported
                # but never used. Now applied: if the list is populated in config,
                # only include articles from those domains.
                # Falls back to accepting all domains if list is empty (safe default).
                if INDIAN_NEWS_DOMAINS:
                    source_lower = source.lower()
                    domain_from_url = self._extract_domain(link)
                    is_indian_source = any(
                        domain in source_lower or domain in domain_from_url
                        for domain in INDIAN_NEWS_DOMAINS
                    )
                    if not is_indian_source:
                        if DEBUG_MODE:
                            print(
                                f"  Filtered non-Indian source: {source} | {title[:50]}")
                        continue

                found_keywords = [
                    kw for kw in NEGATIVE_KEYWORDS
                    if kw in title_lower
                ]
                is_negative = len(found_keywords) > 0

                items.append(NewsItem(
                    title=title,
                    url=link,
                    date=pub_date,
                    source=source,
                    is_negative=is_negative,
                    keywords_found=found_keywords
                ))

            if DEBUG_MODE:
                print(
                    f"  Google News: {len(items)} relevant articles for '{query}'")

        except requests.exceptions.Timeout:
            print("  Google News timeout")
        except Exception as e:
            if DEBUG_MODE:
                print(f"  Google News error: {e}")

        return items

    def _extract_domain(self, url: str) -> str:
        """Extract bare domain from a URL for domain filtering."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower().replace("www.", "")
        except Exception:
            return ""

    def _check_mca(self, company_name: str) -> List[dict]:
        charges = []
        try:
            url = "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do"
            response = self.session.get(
                url, params={"companyName": company_name}, timeout=8
            )
            if response.status_code == 200:
                text = response.text.lower()
                if "charge" in text and "satisfied" not in text:
                    charges.append({
                        "type": "Unsatisfied Charge",
                        "source": "MCA21",
                        "details": "Charge registered — verify amount",
                        "risk_level": "Medium"
                    })
        except Exception as e:
            if DEBUG_MODE:
                print(f"  MCA error: {e}")
        return charges

    def _check_ecourts(self, company_name: str) -> List[str]:
        cases = []
        try:
            url = "https://services.ecourts.gov.in/ecourtindia_v6/"
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                if company_name.lower() in response.text.lower():
                    cases.append(
                        f"Potential case found for {company_name}"
                    )
        except Exception as e:
            if DEBUG_MODE:
                print(f"  e-Courts error: {e}")
        return cases

    def _check_rbi_sebi(self, company_name: str) -> List[str]:
        actions = []
        try:
            url = "https://www.rbi.org.in/Scripts/EnforcementActions.aspx"
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                if company_name.lower() in response.text.lower():
                    actions.append(
                        f"RBI enforcement action found for {company_name}"
                    )
        except Exception as e:
            if DEBUG_MODE:
                print(f"  RBI error: {e}")
        try:
            url = "https://www.sebi.gov.in/enforcement/orders.html"
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                if company_name.lower() in response.text.lower():
                    actions.append(
                        f"SEBI order found for {company_name}"
                    )
        except Exception as e:
            if DEBUG_MODE:
                print(f"  SEBI error: {e}")
        return actions

    def _build_summary(self, findings: ResearchFindings) -> str:
        lines = []
        total_news = (
            len(findings.negative_news) + len(findings.positive_news)
        )
        if total_news == 0:
            lines.append("No significant news coverage found.")
        else:
            lines.append(
                f"Found {total_news} articles: "
                f"{len(findings.negative_news)} negative, "
                f"{len(findings.positive_news)} positive. "
                f"News risk score: {findings.news_risk_score}/10."
            )
            if findings.negative_news:
                lines.append(
                    f"Top negative: '{findings.negative_news[0].title[:80]}'"
                )
        if findings.litigation_found:
            lines.append(
                f"Litigation: {len(findings.litigation_details)} case(s)."
            )
        else:
            lines.append("No litigation found.")
        if findings.mca_charges:
            lines.append(f"MCA: {len(findings.mca_charges)} charge(s).")
        else:
            lines.append("No MCA charges.")
        if findings.rbi_sebi_actions:
            lines.append(
                f"ALERT: {len(findings.rbi_sebi_actions)} RBI/SEBI action(s)."
            )
        else:
            lines.append("No RBI/SEBI actions.")
        return " ".join(lines)


if __name__ == "__main__":
    agent = ResearchAgent()

    print("="*50)
    print("TEST 1: Live Research")
    print("="*50)
    findings = agent.research("Reliance Industries")
    print(f"News Risk Score: {findings.news_risk_score}/10")
    print(f"Summary: {findings.research_summary}")

    print("\n" + "="*50)
    print("TEST 2: Mock Research (High Risk)")
    print("="*50)
    mock = agent.research_with_mock("XYZ Industries Pvt Ltd", "high")
    print(f"News Risk Score: {mock.news_risk_score}/10")
    print(f"Negative News:  {len(mock.negative_news)}")
    print(f"Litigation:     {mock.litigation_found}")
    print(f"MCA Charges:    {len(mock.mca_charges)}")
    print(f"RBI/SEBI:       {len(mock.rbi_sebi_actions)}")
    print(f"Summary: {mock.research_summary}")
