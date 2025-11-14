from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "virtual_worldwide.html"
LIST_FILE = ROOT / "virtual_worldwide.txt"

CUSTOM_TITLES = {
    "https://www.youtube.com/@mlforproteinengineeringsem6420": "ML for Protein Engineering Seminar",
    "https://www.bpdmc.org/": "BPDMC (Boston Protein Data Mining Consortium)",
    "https://www.youtube.com/@SBGridTV": "SBGrid TV",
    "https://www.proteinsociety.org/webinars": "Protein Society Webinars",
    "https://aihealth.duke.edu/events/": "Duke AI Health Events",
    "https://www.massgeneralbrigham.org/en/research-and-innovation/centers-and-programs/artificial-intelligence/educational-activities/artificial-intelligence-for-clinicians": "MGB AI for Clinicians",
    "https://www.psiweb.org/events/event-item/2025/09/23/default-calendar/pre-clinical-sig-webinar-ai-agents-for-drug-discovery-and-development": "Pre-Clinical SIG Webinar: AI Agents for Drug Discovery",
    "https://sites.google.com/view/ocis/home": "Online Computational Immunology Seminars",
    "https://www.youtube.com/@CAUSALab": "CAUSA Lab",
    "https://genbio.ai/fm4bio-seminar/": "GenBio AI Seminar",
    "https://snap.stanford.edu/ai-bio-seminar/": "Stanford AI-Bio Seminar",
    "https://statsupai.org/quarto_web/site/posts/StatsUP-AI%20Statistical%20and%20AI%20Methods%20for%20Health%20Data%20Science%20Seminars.html": "StatsUP AI Seminars",
    "https://ai.ucsf.edu/seminar-series-implementation-and-evaluation-ai-real-world-clinical-settings": "UCSF AI Seminar Series",
    "https://bioinformatics.ccr.cancer.gov/btep/seminar/": "NCI BTEP Bioinformatics Seminar",
    "https://www.youtube.com/@compbioskillsseminarucberk3446/videos": "CompBio Skills Seminar (UC Berkeley)",
    "https://www.youtube.com/@dfcidatascience/videos": "DFCI Data Science",
    "https://www.youtube.com/playlist?list=PLkt0Sm-85E-JnWdnXQnExMoLHEnyoJ7aF": "AI + Biology Seminar Playlist",
    "https://www.youtube.com/@harvardcmsa7486/featured": "Harvard CMSA",
    "https://www.youtube.com/@harvarddatascienceinitiati3320": "Harvard Data Science Initiative",
    "https://www.youtube.com/@KempnerInstitute/videos": "Kempner Institute",
    "https://www.youtube.com/@mlcbconf/featured": "MLCB Conference",
    "https://www.youtube.com/@stanfordmedai": "Stanford Medicine AI",
    "https://hai.stanford.edu/events": "Stanford HAI Events",
    "https://aimi.stanford.edu/upcoming-events/seminars": "Stanford AIMI Events",
    "https://www.youtube.com/@StanfordAIMI": "Stanford AIMI Channel",
    "https://www.youtube.com/@vectorinstituteai/videos": "Vector Institute AI",
    "https://www.youtube.com/@stanfordonline": "Stanford Online",
    "https://www.youtube.com/@SimonsInstitute/videos": "Simons Institute",
    "https://www.globalimmunotalks.org/mission": "Global ImmunoTalks",
    "https://www.rnasociety.org/rna-collaborative-seminar-series": "RNA Collaborative Seminar Series",
    "https://www.oligotherapeutics.org/webinars/": "Oligo Therapeutics Webinars",
}

CUSTOM_DESCRIPTIONS = {
    "https://www.massgeneralbrigham.org/en/research-and-innovation/centers-and-programs/artificial-intelligence/educational-activities/artificial-intelligence-for-clinicians": "Educational offerings from Mass General Brigham's Artificial Intelligence for Clinicians program.",
    "https://www.psiweb.org/events/event-item/2025/09/23/default-calendar/pre-clinical-sig-webinar-ai-agents-for-drug-discovery-and-development": "Pre-Clinical Special Interest Group webinar exploring AI agents for drug discovery and development.",
}


def load_urls(path: Path):
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def normalise_title(raw: str) -> str:
    cleaned = raw.replace("-", " ").replace("_", " ").strip(" /")
    return cleaned.title() if cleaned else "Virtual Event"


def youtube_title(url: str, parsed):
    if "@" in url:
        return url.split("@", 1)[1].split("/")[0]
    for key in ("channel/", "user/", "c/"):
        if key in url:
            return url.split(key, 1)[1].split("/")[0]
    if parsed.path.strip("/"):
        return parsed.path.strip("/")
    return parsed.netloc.split(".")[0]


def generic_title(url: str, parsed):
    segments = [seg for seg in parsed.path.split("/") if seg]
    generic_tokens = {"events", "event", "calendar", "home", "index", "view", "videos"}

    for segment in reversed(segments):
        cleaned = segment.strip()
        if cleaned and cleaned.lower() not in generic_tokens:
            return cleaned
    return parsed.netloc


def build_card(soup: BeautifulSoup, url: str):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    is_youtube = "youtube.com" in domain or "youtu.be" in domain

    title = youtube_title(url, parsed) if is_youtube else generic_title(url, parsed)
    title = normalise_title(title)
    title = CUSTOM_TITLES.get(url, title)

    badge_class = "youtube-badge" if is_youtube else "seminar-badge"
    badge_icon = "fab fa-youtube" if is_youtube else "fas fa-chalkboard-teacher"
    badge_text = "YOUTUBE" if is_youtube else "SEMINAR"
    btn_text = "Visit Channel" if is_youtube else "Visit Site"

    col = soup.new_tag("div", **{"class": "col-md-6 col-lg-4"})
    card = soup.new_tag("div", **{"class": "card virtual-event-card h-100"})
    body = soup.new_tag("div", **{"class": "card-body d-flex flex-column"})

    badge_row = soup.new_tag("div", **{"class": "d-flex justify-content-between align-items-start mb-3"})
    badge_span = soup.new_tag("span", **{"class": f"badge event-type-badge {badge_class}"})
    badge_icon_tag = soup.new_tag("i", **{"class": f"{badge_icon} me-1"})
    badge_span.append(badge_icon_tag)
    badge_span.append(badge_text)
    badge_row.append(badge_span)

    h5 = soup.new_tag("h5", **{"class": "card-title"})
    h5.string = title

    desc = soup.new_tag("p", **{"class": "card-text text-muted"})
    desc.string = CUSTOM_DESCRIPTIONS.get(
        url,
        "Visit the source for more information about this virtual event."
    )

    btn_container = soup.new_tag("div", **{"class": "mt-auto"})
    link = soup.new_tag(
        "a",
        href=url,
        target="_blank",
        rel="noopener noreferrer",
        **{"class": "btn btn-outline-primary btn-sm"}
    )
    link_icon = soup.new_tag("i", **{"class": "fas fa-external-link-alt me-1"})
    link.append(link_icon)
    link.append(btn_text)
    btn_container.append(link)

    body.extend([badge_row, h5, desc, btn_container])
    card.append(body)
    col.append(card)
    return col


def update_template(template: Path, urls):
    soup = BeautifulSoup(template.read_text(), "html.parser")

    # remove refresh button/status if still present
    btn = soup.find(id="refreshVirtualEventsBtn")
    if btn:
        btn.decompose()
    status = soup.find(id="virtualWorldwideStatus")
    if status:
        status.decompose()

    grid = soup.find(id="virtualEventsGrid")
    if not grid:
        raise RuntimeError("Could not find #virtualEventsGrid in template")
    grid.clear()

    for url in urls:
        grid.append(build_card(soup, url))

    # drop reference to the old client script if any
    for script in soup.find_all("script"):
        if script.get("src") and "virtual_worldwide.js" in script["src"]:
            script.decompose()

    template.write_text(str(soup))


def main():
    urls = load_urls(LIST_FILE)
    update_template(TEMPLATE, urls)
    print(f"Updated template with {len(urls)} cards from virtual_worldwide.txt")


if __name__ == "__main__":
    main()
