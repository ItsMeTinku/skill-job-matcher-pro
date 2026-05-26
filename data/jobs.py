"""
data/jobs.py — Curated job dataset
=====================================
25 job listings across 6 technology categories.
Each entry includes:
  - title
  - rich description (used for semantic embedding)
  - required_skills list
  - category
  - experience_level

The description text is intentionally rich with synonyms and context so
the sentence-transformer model can match it accurately against resume text.
"""

JOB_DATASET = [

    # ── Python / Backend ─────────────────────────────────────────────
    {
        "title": "Python Backend Developer",
        "description": (
            "Build and maintain scalable Python REST APIs using Flask or Django frameworks. "
            "Design relational database schemas with PostgreSQL and SQLAlchemy ORM. "
            "Write clean, testable code following PEP-8 and SOLID principles. "
            "Implement authentication, rate limiting, and secure session management. "
            "Deploy services on AWS or GCP using Docker containers and CI/CD pipelines."
        ),
        "required_skills": [
            "python", "flask", "django", "postgresql", "sql", "rest api",
            "sqlalchemy", "docker", "aws", "git",
        ],
        "category": "Backend Development",
        "experience_level": "Mid",
    },
    {
        "title": "Senior Python Engineer",
        "description": (
            "Lead the design and development of high-performance Python microservices. "
            "Mentor junior engineers, conduct code reviews, and enforce engineering standards. "
            "Architect distributed systems using message queues like RabbitMQ or Kafka. "
            "Optimise database queries, caching strategies with Redis, and API performance. "
            "Experience with async Python frameworks such as FastAPI or asyncio."
        ),
        "required_skills": [
            "python", "fastapi", "microservices", "redis", "kafka",
            "postgresql", "docker", "kubernetes", "aws", "system design",
        ],
        "category": "Backend Development",
        "experience_level": "Senior",
    },
    {
        "title": "Junior Python Developer",
        "description": (
            "Assist the backend team in building Python web applications using Flask. "
            "Write unit tests with pytest, fix bugs, and implement small features. "
            "Work with SQL databases — write queries and design simple schemas. "
            "Collaborate using Git version control and participate in Agile sprint ceremonies."
        ),
        "required_skills": [
            "python", "flask", "sql", "git", "html", "css", "pytest",
        ],
        "category": "Backend Development",
        "experience_level": "Junior",
    },

    # ── Frontend / Web ───────────────────────────────────────────────
    {
        "title": "React Frontend Developer",
        "description": (
            "Build responsive, performant single-page applications with React and TypeScript. "
            "Manage global state using Redux or Zustand. Consume REST and GraphQL APIs. "
            "Implement responsive layouts with CSS Flexbox, Grid, and Tailwind CSS. "
            "Write component tests with Jest and React Testing Library. "
            "Collaborate closely with UI/UX designers using Figma."
        ),
        "required_skills": [
            "react", "javascript", "typescript", "redux", "html", "css",
            "tailwind", "graphql", "jest", "figma",
        ],
        "category": "Frontend Development",
        "experience_level": "Mid",
    },
    {
        "title": "Full Stack Web Developer",
        "description": (
            "Develop complete web features across both frontend and backend. "
            "Build React or Vue.js interfaces and Python or Node.js APIs. "
            "Manage PostgreSQL and MongoDB databases. "
            "Deploy applications on cloud platforms and configure CI/CD workflows. "
            "Write clean, documented code and participate in pair programming sessions."
        ),
        "required_skills": [
            "react", "javascript", "python", "node.js", "postgresql",
            "mongodb", "html", "css", "docker", "git",
        ],
        "category": "Full Stack Development",
        "experience_level": "Mid",
    },
    {
        "title": "Vue.js Frontend Engineer",
        "description": (
            "Create interactive UIs using Vue 3 with the Composition API and Pinia store. "
            "Build and maintain a shared component library using Storybook. "
            "Integrate with RESTful APIs using Axios. Optimise Core Web Vitals. "
            "Work with SCSS and BEM methodology for maintainable styling."
        ),
        "required_skills": [
            "vue.js", "javascript", "typescript", "html", "css", "scss",
            "rest api", "git", "pinia",
        ],
        "category": "Frontend Development",
        "experience_level": "Mid",
    },

    # ── Data Science / ML ────────────────────────────────────────────
    {
        "title": "Data Scientist",
        "description": (
            "Develop and deploy machine learning models to solve business problems. "
            "Perform exploratory data analysis with Pandas, NumPy, and Matplotlib. "
            "Build classification, regression, and clustering models using scikit-learn. "
            "Work with large datasets stored in PostgreSQL and AWS S3. "
            "Communicate insights clearly through visualisations and presentations."
        ),
        "required_skills": [
            "python", "machine learning", "pandas", "numpy", "scikit-learn",
            "matplotlib", "sql", "statistics", "data analysis", "aws",
        ],
        "category": "Data Science",
        "experience_level": "Mid",
    },
    {
        "title": "Machine Learning Engineer",
        "description": (
            "Build production-ready ML pipelines for training, evaluation, and deployment. "
            "Fine-tune large language models and deep learning architectures using PyTorch. "
            "Design feature engineering pipelines and manage datasets with DVC. "
            "Deploy models as REST APIs with FastAPI and monitor performance with MLflow. "
            "Work with NLP tasks: text classification, named entity recognition, embeddings."
        ),
        "required_skills": [
            "python", "pytorch", "deep learning", "nlp", "scikit-learn",
            "fastapi", "mlflow", "docker", "transformers", "cuda",
        ],
        "category": "Machine Learning",
        "experience_level": "Senior",
    },
    {
        "title": "AI/NLP Research Engineer",
        "description": (
            "Conduct research and implementation of state-of-the-art NLP models. "
            "Work with transformer architectures — BERT, GPT, and sentence-transformers. "
            "Implement text classification, summarisation, and semantic search systems. "
            "Publish findings, maintain experiment logs, and write technical reports. "
            "Experience with HuggingFace Transformers library and ONNX model export."
        ),
        "required_skills": [
            "python", "nlp", "transformers", "pytorch", "huggingface",
            "deep learning", "machine learning", "numpy", "pandas", "research",
        ],
        "category": "Machine Learning",
        "experience_level": "Senior",
    },
    {
        "title": "Data Analyst",
        "description": (
            "Query and analyse structured data from PostgreSQL and data warehouse systems. "
            "Build dashboards and visualisations in Tableau or Power BI. "
            "Write complex SQL queries, CTEs, and window functions. "
            "Perform cohort analysis, A/B testing analysis, and funnel analysis. "
            "Present data-driven insights to non-technical stakeholders."
        ),
        "required_skills": [
            "sql", "python", "pandas", "excel", "tableau", "power bi",
            "data visualisation", "statistics", "postgresql",
        ],
        "category": "Data Science",
        "experience_level": "Junior",
    },

    # ── DevOps / Cloud ───────────────────────────────────────────────
    {
        "title": "DevOps Engineer",
        "description": (
            "Design and maintain CI/CD pipelines using GitHub Actions or Jenkins. "
            "Manage containerised workloads with Docker and Kubernetes (EKS, GKE). "
            "Provision and manage cloud infrastructure on AWS using Terraform and Ansible. "
            "Monitor system health with Prometheus, Grafana, and ELK stack. "
            "Implement blue-green deployments and automated rollback strategies."
        ),
        "required_skills": [
            "docker", "kubernetes", "aws", "terraform", "ansible",
            "ci/cd", "linux", "bash", "prometheus", "grafana",
        ],
        "category": "DevOps & Cloud",
        "experience_level": "Mid",
    },
    {
        "title": "Cloud Infrastructure Engineer",
        "description": (
            "Architect and manage cloud-native solutions on AWS, Azure, or GCP. "
            "Implement infrastructure as code using Terraform and CloudFormation. "
            "Manage networking — VPCs, subnets, security groups, load balancers. "
            "Optimise cloud costs through right-sizing and reserved instance strategies. "
            "Ensure high availability, disaster recovery, and security compliance."
        ),
        "required_skills": [
            "aws", "azure", "gcp", "terraform", "networking",
            "kubernetes", "docker", "linux", "python", "security",
        ],
        "category": "DevOps & Cloud",
        "experience_level": "Senior",
    },
    {
        "title": "Site Reliability Engineer (SRE)",
        "description": (
            "Maintain SLOs and SLAs for high-traffic distributed systems. "
            "Build tooling for automated incident response and alerting. "
            "Perform capacity planning, load testing, and performance tuning. "
            "Write runbooks and conduct blameless post-mortems. "
            "Strong programming skills in Python or Go for automation and tooling."
        ),
        "required_skills": [
            "python", "golang", "kubernetes", "docker", "aws",
            "monitoring", "prometheus", "linux", "ci/cd", "incident management",
        ],
        "category": "DevOps & Cloud",
        "experience_level": "Senior",
    },

    # ── Mobile Development ───────────────────────────────────────────
    {
        "title": "Android Developer",
        "description": (
            "Build and ship Android applications using Kotlin and Jetpack Compose. "
            "Implement MVVM architecture with ViewModel, LiveData, and Room database. "
            "Integrate REST APIs using Retrofit and Coroutines for async operations. "
            "Write UI tests with Espresso and unit tests with JUnit and Mockito. "
            "Publish and manage apps on Google Play Store."
        ),
        "required_skills": [
            "kotlin", "android", "java", "jetpack compose", "room",
            "retrofit", "mvvm", "git", "firebase",
        ],
        "category": "Mobile Development",
        "experience_level": "Mid",
    },
    {
        "title": "iOS Developer",
        "description": (
            "Develop native iOS applications using Swift and SwiftUI. "
            "Implement MVC and MVVM design patterns with Combine for reactive programming. "
            "Integrate Core Data for local persistence and REST APIs with URLSession. "
            "Submit and maintain apps on Apple App Store, manage provisioning profiles. "
            "Conduct code reviews and mentor junior mobile developers."
        ),
        "required_skills": [
            "swift", "ios", "swiftui", "xcode", "core data",
            "combine", "rest api", "git", "mvvm",
        ],
        "category": "Mobile Development",
        "experience_level": "Mid",
    },
    {
        "title": "Flutter Developer",
        "description": (
            "Build cross-platform mobile applications for iOS and Android using Flutter. "
            "Manage application state with Bloc or Riverpod patterns. "
            "Integrate Firebase for authentication, Firestore, and cloud messaging. "
            "Work with REST APIs and gRPC. Write widget and integration tests."
        ),
        "required_skills": [
            "flutter", "dart", "firebase", "rest api", "bloc",
            "ios", "android", "git",
        ],
        "category": "Mobile Development",
        "experience_level": "Junior",
    },

    # ── Security / Database ──────────────────────────────────────────
    {
        "title": "Cybersecurity Analyst",
        "description": (
            "Monitor and defend systems against cyber threats using SIEM platforms. "
            "Conduct vulnerability assessments and penetration testing. "
            "Respond to security incidents, perform forensic analysis, and write reports. "
            "Implement and audit network security controls — firewalls, IDS/IPS, VPNs. "
            "Knowledge of OWASP top-10, CVE databases, and compliance frameworks."
        ),
        "required_skills": [
            "networking", "security", "linux", "penetration testing",
            "python", "siem", "firewall", "owasp", "vulnerability assessment",
        ],
        "category": "Cybersecurity",
        "experience_level": "Mid",
    },
    {
        "title": "Database Administrator (DBA)",
        "description": (
            "Design, implement, and maintain PostgreSQL and MySQL database systems. "
            "Write complex queries, stored procedures, and optimise query performance. "
            "Implement backup, replication, and high-availability strategies. "
            "Monitor database health, tune configuration parameters, and manage indexes. "
            "Work with cloud databases such as AWS RDS and Google Cloud SQL."
        ),
        "required_skills": [
            "postgresql", "mysql", "sql", "database design", "backup",
            "replication", "aws rds", "performance tuning", "linux",
        ],
        "category": "Database",
        "experience_level": "Senior",
    },

    # ── Design / Product ─────────────────────────────────────────────
    {
        "title": "UI/UX Designer",
        "description": (
            "Design intuitive user interfaces and seamless user experiences for web and mobile. "
            "Conduct user research, usability testing, and build customer journey maps. "
            "Create wireframes, prototypes, and high-fidelity mockups in Figma. "
            "Maintain and evolve the product design system and component library. "
            "Collaborate with engineers to ensure pixel-perfect implementation."
        ),
        "required_skills": [
            "figma", "ui design", "ux research", "prototyping",
            "design systems", "user testing", "css", "html",
        ],
        "category": "Design",
        "experience_level": "Mid",
    },

    # ── Blockchain / Web3 ────────────────────────────────────────────
    {
        "title": "Blockchain Developer",
        "description": (
            "Develop and audit smart contracts in Solidity for Ethereum and EVM chains. "
            "Build decentralised applications (DApps) with Web3.js or Ethers.js. "
            "Integrate smart contracts with React frontends and IPFS storage. "
            "Write comprehensive tests using Hardhat and Foundry frameworks. "
            "Understand DeFi protocols, token standards (ERC-20, ERC-721)."
        ),
        "required_skills": [
            "solidity", "ethereum", "blockchain", "web3.js", "javascript",
            "react", "hardhat", "defi", "git",
        ],
        "category": "Blockchain",
        "experience_level": "Mid",
    },

    # ── Software Engineering ─────────────────────────────────────────
    {
        "title": "Java Backend Engineer",
        "description": (
            "Build enterprise-grade backend services with Java 17+ and Spring Boot. "
            "Design RESTful and event-driven APIs using Spring MVC and Kafka. "
            "Work with Hibernate ORM and JPA for database interactions with PostgreSQL. "
            "Write integration and unit tests using JUnit 5 and Mockito. "
            "Deploy microservices on Kubernetes with Helm charts."
        ),
        "required_skills": [
            "java", "spring boot", "spring mvc", "hibernate", "postgresql",
            "kafka", "docker", "kubernetes", "junit", "rest api",
        ],
        "category": "Backend Development",
        "experience_level": "Mid",
    },
    {
        "title": "C++ Systems Programmer",
        "description": (
            "Develop high-performance systems software, game engines, or embedded applications. "
            "Write modern C++17/20 code with emphasis on memory safety and efficiency. "
            "Design and implement data structures and algorithms for performance-critical paths. "
            "Work with multi-threading, concurrency primitives, and low-level OS APIs. "
            "Profiling and optimising code with tools like Valgrind and perf."
        ),
        "required_skills": [
            "c++", "data structures", "algorithms", "multithreading",
            "linux", "cmake", "git", "memory management",
        ],
        "category": "Systems Programming",
        "experience_level": "Senior",
    },
    {
        "title": "Game Developer (Unity)",
        "description": (
            "Design and implement gameplay systems, physics, and AI for mobile and PC games. "
            "Write performant C# scripts in Unity for character controllers, UI, and game logic. "
            "Optimise game assets, build pipelines, and manage addressable assets. "
            "Integrate Unity Ads, In-App Purchases, and multiplayer networking with Photon."
        ),
        "required_skills": [
            "unity", "c#", "game design", "c++", "3d modelling",
            "physics", "networking", "git",
        ],
        "category": "Game Development",
        "experience_level": "Mid",
    },
    {
        "title": "Digital Marketing Engineer",
        "description": (
            "Implement and optimise SEO strategies — technical SEO, on-page, and off-page. "
            "Set up marketing analytics with Google Analytics 4, Tag Manager, and Mixpanel. "
            "Build marketing automation workflows and manage email campaigns. "
            "Analyse funnel data, run A/B tests, and report on conversion rate optimisation. "
            "Manage paid search (Google Ads) and social media campaigns."
        ),
        "required_skills": [
            "seo", "google analytics", "marketing", "google ads",
            "a/b testing", "email marketing", "data analysis", "html", "css",
        ],
        "category": "Marketing",
        "experience_level": "Junior",
    },
]
