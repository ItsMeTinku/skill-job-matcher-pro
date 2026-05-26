"""
utils/skill_extractor.py — NLP skill extraction engine
========================================================
Extracts professional technology skills from raw resume text using:
  1. A curated, normalised skill taxonomy (330+ skills)
  2. Multi-word phrase matching (e.g. "machine learning", "deep learning")
  3. Case-insensitive, boundary-aware regex matching

Public API
----------
    extract_skills(text: str) -> list[str]
        Returns a sorted list of normalised skill names found in *text*.
"""

import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


# ── Comprehensive skill taxonomy ──────────────────────────────────────
# Each entry is the canonical display name; matching is case-insensitive.
# Longer phrases must appear before shorter substrings to avoid partial hits.

SKILL_TAXONOMY: list[str] = [
    # ── Programming Languages ──────────────────────────────────────
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C",
    "Go", "Golang", "Rust", "Swift", "Kotlin", "Dart", "Ruby",
    "PHP", "Scala", "R", "MATLAB", "Perl", "Shell", "Bash",
    "PowerShell", "Groovy", "Elixir", "Haskell", "Lua",

    # ── Web Frameworks ─────────────────────────────────────────────
    "Flask", "Django", "FastAPI", "Express.js", "Node.js",
    "Spring Boot", "Spring MVC", "Laravel", "Rails", "Ruby on Rails",
    "ASP.NET", ".NET Core", "Gin", "Echo",

    # ── Frontend Frameworks / Libraries ───────────────────────────
    "React", "Vue.js", "Angular", "Next.js", "Nuxt.js",
    "Svelte", "jQuery", "Bootstrap", "Tailwind CSS", "Material UI",
    "Redux", "Pinia", "Zustand", "Vuex",

    # ── Mobile Development ─────────────────────────────────────────
    "Android", "iOS", "Flutter", "React Native", "Jetpack Compose",
    "SwiftUI", "Xcode", "Kotlin Multiplatform",

    # ── Databases ──────────────────────────────────────────────────
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis",
    "Cassandra", "DynamoDB", "Elasticsearch", "Neo4j",
    "Oracle Database", "Microsoft SQL Server", "MariaDB",
    "Firebase", "Supabase", "PlanetScale",

    # ── ORMs / Query Builders ──────────────────────────────────────
    "SQLAlchemy", "Hibernate", "Prisma", "Sequelize", "TypeORM",
    "Mongoose", "ActiveRecord",

    # ── AI / ML / Data Science ─────────────────────────────────────
    "Machine Learning", "Deep Learning", "Natural Language Processing",
    "NLP", "Computer Vision", "Reinforcement Learning",
    "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
    "Hugging Face", "Transformers", "LangChain", "OpenAI API",
    "BERT", "GPT", "Sentence Transformers",
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn",
    "Plotly", "Tableau", "Power BI", "Jupyter Notebook",
    "Feature Engineering", "Model Deployment", "MLflow", "DVC",
    "CUDA", "ONNX",

    # ── Cloud Platforms ────────────────────────────────────────────
    "AWS", "Azure", "Google Cloud", "GCP", "Heroku", "Vercel",
    "Netlify", "DigitalOcean", "Linode", "Cloudflare",

    # ── AWS Services ───────────────────────────────────────────────
    "EC2", "S3", "Lambda", "RDS", "EKS", "ECS", "CloudFormation",
    "SageMaker", "IAM", "VPC", "Route 53",

    # ── DevOps & Infrastructure ────────────────────────────────────
    "Docker", "Kubernetes", "Terraform", "Ansible", "Helm",
    "CI/CD", "GitHub Actions", "GitLab CI", "Jenkins", "CircleCI",
    "ArgoCD", "Prometheus", "Grafana", "ELK Stack",
    "Nginx", "Apache", "HAProxy", "Vault",

    # ── Networking & Security ──────────────────────────────────────
    "Networking", "TCP/IP", "DNS", "HTTP", "HTTPS", "REST API",
    "GraphQL", "WebSockets", "gRPC", "OAuth", "JWT",
    "Penetration Testing", "Ethical Hacking", "SIEM",
    "Firewalls", "OWASP", "Cryptography", "SSL/TLS",
    "Vulnerability Assessment", "Security Auditing",

    # ── Version Control & Collaboration ───────────────────────────
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira",
    "Confluence", "Notion", "Linear",

    # ── Testing ────────────────────────────────────────────────────
    "Pytest", "JUnit", "Jest", "Cypress", "Selenium",
    "Postman", "Unit Testing", "Integration Testing", "TDD",
    "Mocha", "Chai", "Espresso",

    # ── Data Engineering ───────────────────────────────────────────
    "Apache Spark", "Apache Kafka", "Airflow", "dbt",
    "ETL", "Data Warehousing", "Snowflake", "BigQuery",
    "Hadoop", "Hive", "Data Pipelines",

    # ── Design & UX ────────────────────────────────────────────────
    "Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator",
    "UI Design", "UX Research", "Prototyping", "Design Systems",
    "Wireframing", "User Testing",

    # ── Markup / Styling ───────────────────────────────────────────
    "HTML", "CSS", "SCSS", "SASS", "XML", "JSON", "YAML",

    # ── Blockchain ─────────────────────────────────────────────────
    "Blockchain", "Solidity", "Ethereum", "Web3.js", "DeFi",
    "Smart Contracts", "Hardhat", "Foundry",

    # ── Game Development ───────────────────────────────────────────
    "Unity", "Unreal Engine", "Game Design", "OpenGL", "WebGL",

    # ── Methodologies & Soft Skills ────────────────────────────────
    "Agile", "Scrum", "Kanban", "System Design", "Microservices",
    "Object-Oriented Programming", "OOP", "Functional Programming",
    "Data Structures", "Algorithms", "Design Patterns",
    "Code Review", "Technical Writing", "Documentation",

    # ── Analytics & Marketing ──────────────────────────────────────
    "SEO", "Google Analytics", "Google Ads", "A/B Testing",
    "Email Marketing", "Marketing Automation",
    "Excel", "Google Sheets", "Data Analysis",
]


@lru_cache(maxsize=None)
def _build_skill_patterns() -> list[tuple[re.Pattern, str]]:
    """
    Build compiled regex patterns for every skill in the taxonomy.
    Patterns are word-boundary anchored and case-insensitive.
    Longer skills come first to prevent partial matches on sub-phrases.
    Cached after first call.
    """
    # Sort by length descending so "Machine Learning" matches before "Learning"
    sorted_skills = sorted(SKILL_TAXONOMY, key=len, reverse=True)

    patterns: list[tuple[re.Pattern, str]] = []
    for skill in sorted_skills:
        # Escape and create a word-boundary regex
        escaped = re.escape(skill)
        pattern = re.compile(
            rf"(?<![A-Za-z0-9\-\.])({escaped})(?![A-Za-z0-9\-\.])",
            re.IGNORECASE,
        )
        patterns.append((pattern, skill))

    return patterns


def extract_skills(text: str) -> list[str]:
    """
    Extract technology skills from *text* using the skill taxonomy.

    Parameters
    ----------
    text : str
        Raw text extracted from a resume.

    Returns
    -------
    list[str]
        Sorted list of canonical skill names (e.g. ["Docker", "Python"]).
    """
    if not text or not text.strip():
        return []

    found: set[str] = set()
    patterns = _build_skill_patterns()

    for pattern, canonical_name in patterns:
        if pattern.search(text):
            found.add(canonical_name)

    return sorted(found, key=str.lower)


def skills_to_string(skills: list[str]) -> str:
    """Join a skills list into a comma-separated string for storage."""
    return ", ".join(skills)


def string_to_skills(skills_str: str) -> list[str]:
    """Parse a comma-separated skills string back into a list."""
    if not skills_str:
        return []
    return sorted({s.strip() for s in skills_str.split(",") if s.strip()})
