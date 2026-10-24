import re
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin

from .official_fetch import validate_official_url
from .sources import JobItem, SourceDefinition, clean, parse_all_dates, parse_explicit_deadline, parse_html

_EXCLUDED = (
    'result', 'results', 'admit card', 'call letter', 'answer key', 'interview schedule',
    'shortlisted', 'selected candidates', 'selection list', 'marks', 'score card',
    'corrigendum', 'addendum', 'cancellation', 'cancelled', 'document verification',
    'exam city', 'response sheet', 'notice regarding exam', 'final result',
)

_RECRUITMENT = re.compile(
    r'\b(recruitment|vacanc(?:y|ies)|current openings?|career opportunities?|'
    r'engagement of|applications? invited|apply online|advertisement|advt\.?|'
    r'probationary officer|junior associate|specialist cadre|officer grade|'
    r'assistant manager|manager grade|teaching posts?|non[- ]teaching posts?|'
    r'faculty posts?|staff recruitment)\b',
    re.I,
)



class _SBIPageParser(HTMLParser):
    """Keep each SBI recruitment heading paired with its own ad and apply links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_title = ""
        self.current_advertisement = None
        self.current_notice_url = None
        self.paragraph = None
        self.list_item = None
        self.anchor = None
        self.records = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"p", "h2", "h3", "h4"}:
            self.paragraph = []
        elif tag == "li":
            self.list_item = {"text": [], "links": []}
        elif tag == "a":
            self.anchor = {"href": attributes.get("href", ""), "text": []}

    def handle_data(self, data):
        if self.paragraph is not None:
            self.paragraph.append(data)
        if self.list_item is not None:
            self.list_item["text"].append(data)
        if self.anchor is not None:
            self.anchor["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            if self.list_item is not None:
                self.list_item["links"].append({
                    "href": self.anchor["href"],
                    "text": clean(" ".join(self.anchor["text"])),
                })
            self.anchor = None
        elif tag in {"p", "h2", "h3", "h4"} and self.paragraph is not None:
            text = clean(" ".join(self.paragraph))
            self.paragraph = None
            advert = re.search(r"advertisement\\s*(?:no\\.?|number)\\s*[:#-]?\\s*([A-Z0-9/-]+)", text, re.I)
            if advert:
                self.current_advertisement = advert.group(1).rstrip(".,)")
            elif _RECRUITMENT.search(text) and not any(term in text.lower() for term in _EXCLUDED):
                self.current_title = re.sub(r"\\s*\\((?:apply online|online registration).*?\\)\\s*$", "", text, flags=re.I).strip()
                self.current_advertisement = None
                self.current_notice_url = None
        elif tag == "li" and self.list_item is not None:
            label = clean(" ".join(self.list_item["text"]))
            for link in self.list_item["links"]:
                link_text = clean(link["text"])
                href = clean(link["href"])
                if not href:
                    continue
                lowered = link_text.lower()
                if "download advertisement" in lowered and ("english" in lowered or not self.current_notice_url):
                    candidate = urljoin("https://sbi.bank.in/web/careers/current-openings", href)
                    try:
                        validate_official_url(candidate)
                    except ValueError:
                        continue
                    self.current_notice_url = candidate
                if not re.search(r"\\bapply online\\b", lowered):
                    continue
                title = self.current_title
                if not title or any(term in f"{title} {link_text}".lower() for term in _EXCLUDED):
                    continue
                application_url = urljoin("https://sbi.bank.in/web/careers/current-openings", href)
                notice_url = self.current_notice_url
                if not notice_url or notice_url == application_url:
                    continue
                try:
                    validate_official_url(notice_url)
                    validate_official_url(application_url)
                except ValueError:
                    continue
                date_text = f"{title} {link_text}"
                dates = parse_all_dates(date_text)
                deadline = parse_explicit_deadline(date_text)
                if dates and re.search(r"apply online|online registration|registration extended|last date", date_text, re.I):
                    deadline = dates[-1]
                if not deadline or deadline < date.today():
                    continue
                self.records.append(JobItem(
                    external_id=self.current_advertisement or notice_url,
                    title=title[:500],
                    organization="State Bank of India",
                    official_notice_url=notice_url,
                    job_type="government",
                    location="India",
                    application_start_date=dates[0] if len(dates) > 1 else None,
                    deadline=deadline,
                    application_url=application_url,
                    summary="Current recruitment listed on the official SBI Careers page. Confirm post-specific eligibility, vacancies, fee and instructions in the linked advertisement.",
                    confidence=0.96,
                ))
            self.list_item = None


def parse_sbi(html, base_url):
    """Pair SBI current-opening headings, official advertisement PDFs and dated apply links."""
    parser = _SBIPageParser()
    parser.feed(str(html or ""))
    parser.close()
    seen = set()
    result = []
    for item in parser.records:
        identity = (item.external_id, item.official_notice_url, item.application_url)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(item)
    return result


def _generic_official_parser(organization, summary):
    def parse(html, base_url):
        document = parse_html(html)
        items = []
        seen = set()
        today = date.today()

        candidates = []
        for block in document.blocks:
            text = clean(block.get('text'))
            for href in block.get('hrefs', []):
                candidates.append((href, text))
        candidates.extend(document.links)

        for index, (href, text) in enumerate(candidates, start=1):
            text = clean(text)
            lowered = text.lower()
            if not href or len(text) < 8 or not _RECRUITMENT.search(text):
                continue
            if any(term in lowered for term in _EXCLUDED):
                continue
            notice_url = urljoin(base_url, href)
            try:
                validate_official_url(notice_url)
            except ValueError:
                continue
            identity = (text.lower(), notice_url)
            if identity in seen:
                continue
            seen.add(identity)
            deadline = parse_explicit_deadline(text)
            if deadline and deadline < today:
                continue
            is_application_link = bool(re.search(r'\b(apply online|apply now|online application|registration portal)\b', text, re.I))
            application_url = notice_url if is_application_link else None
            items.append(JobItem(
                external_id=f'{organization.lower().replace(" ", "-")}-{index}-{text[:80]}',
                title=text[:500],
                organization=organization,
                official_notice_url=base_url if is_application_link else notice_url,
                location='India',
                deadline=deadline,
                application_url=application_url,
                summary=summary,
                confidence=0.92 if deadline else 0.84,
                warnings=(['notice_is_listing_page'] if is_application_link else []) + ([] if deadline else ['Confirm the closing date and post-specific eligibility in the official recruitment notice.']),
            ))
        return items

    return parse


parse_rbi = _generic_official_parser(
    'Reserve Bank of India (RBI)',
    'Official RBI recruitment opportunity. Confirm eligibility, vacancies, fee, dates and application instructions on the RBI opportunities portal.',
)
parse_sbi = _generic_official_parser(
    'State Bank of India (SBI)',
    'Official SBI recruitment opening. Confirm cadre, eligibility, vacancies, fee, dates and application instructions on SBI Careers.',
)
parse_nvs = _generic_official_parser(
    'Navodaya Vidyalaya Samiti (NVS)',
    'Official NVS recruitment notice. Confirm teaching/non-teaching post details, eligibility, vacancies, fee and dates in the official notice.',
)
parse_sainik = _generic_official_parser(
    'Sainik Schools Society',
    'Official Sainik Schools recruitment notice. Confirm school/post-specific eligibility, employment terms and closing date in the official notice.',
)
parse_kvs = _generic_official_parser(
    'Kendriya Vidyalaya Sangathan (KVS)',
    'Official KVS recruitment notice. Confirm teaching/non-teaching eligibility, vacancies, fee and dates in the official notice.',
)
parse_sebi = _generic_official_parser(
    'Securities and Exchange Board of India (SEBI)',
    'Official SEBI recruitment opportunity. Confirm stream, eligibility, vacancies, fee, dates and application instructions in the official notice.',
)
parse_ibps = _generic_official_parser(
    'Institute of Banking Personnel Selection (IBPS)',
    'Official IBPS recruitment process notice. Confirm participating organisations, eligibility, vacancies, fee and dates in the official notification.',
)
parse_drdo = _generic_official_parser(
    'DRDO Recruitment and Assessment Centre (RAC)',
    'Official DRDO/RAC recruitment opportunity. Confirm discipline, eligibility, vacancies, fee and dates in the official notice.',
)


PRIORITY_OFFICIAL_SOURCES = (
    SourceDefinition('rbi', 'Reserve Bank of India', 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx', parse_rbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sbi', 'State Bank of India — Careers', 'https://sbi.bank.in/web/careers/current-openings', parse_sbi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('nvs', 'Navodaya Vidyalaya Samiti', 'https://navodaya.gov.in/nvs/en/Recruitment/', parse_nvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sainik_schools', 'Sainik Schools Society', 'https://sainikschoolsociety.in/', parse_sainik, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('kvs', 'Kendriya Vidyalaya Sangathan', 'https://kvsangathan.nic.in/en/recruitment/', parse_kvs, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('sebi', 'Securities and Exchange Board of India', 'https://www.sebi.gov.in/sebiweb/other/careerdetail.jsp?careerId=1', parse_sebi, allow_missing_deadline=True, missing_deadline_max_age_days=60),
    SourceDefinition('ibps', 'Institute of Banking Personnel Selection', 'https://www.ibps.in/', parse_ibps, allow_missing_deadline=True, missing_deadline_max_age_days=45),
    SourceDefinition('drdo_rac', 'DRDO Recruitment and Assessment Centre', 'https://rac.gov.in/', parse_drdo, allow_missing_deadline=True, missing_deadline_max_age_days=60),
)
