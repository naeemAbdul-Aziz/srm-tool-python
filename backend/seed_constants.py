"""Seed constants extracted from comprehensive_seed to reduce bloat.

This module provides static data structures: names, schools/programs, course catalog,
and academic calendar. Keeping them separate makes logic changes diff-friendly.
"""
from datetime import date

GHANAIAN_MALE_NAMES = [
    "Kwame", "Kofi", "Kwaku", "Yaw", "Kwadwo", "Kwabena", "Kwesi", "Akwasi",
    "Nana", "Kojo", "Fiifi", "Ato", "Ebo", "Kodwo", "Paa", "Ekow",
    "Nii", "Tetteh", "Lartey", "Adjei", "Richmond", "Emmanuel", "Samuel",
    "Daniel", "Michael", "David", "Joseph", "Francis", "Prince", "Felix",
    "Eric", "Justice", "Bright", "Isaac", "Abraham", "Moses", "John",
    "Godfred", "Benjamin", "Stephen", "Mark", "Paul", "James", "Peter"
]

GHANAIAN_FEMALE_NAMES = [
    "Ama", "Efua", "Akua", "Yaa", "Adwoa", "Abena", "Esi", "Akosua",
    "Adjoa", "Afua", "Afia", "Akoto", "Nana", "Akorfa", "Dzidzor", "Edem",
    "Vivian", "Grace", "Patience", "Mercy", "Comfort", "Charity", "Faith",
    "Joyce", "Linda", "Sandra", "Patricia", "Gifty", "Vida", "Faustina",
    "Joana", "Priscilla", "Gloria", "Eunice", "Rose", "Mary", "Elizabeth",
    "Portia", "Hannah", "Ruth", "Esther", "Deborah", "Sarah", "Rebecca"
]

GHANAIAN_SURNAMES = [
    "Asante", "Mensah", "Osei", "Boateng", "Owusu", "Agyei", "Adjei", "Frimpong",
    "Opoku", "Gyasi", "Nkrumah", "Danso", "Amponsah", "Bediako", "Ofori",
    "Acheampong", "Antwi", "Darko", "Amoah", "Akoto", "Preko", "Sarfo",
    "Tetteh", "Lartey", "Nii", "Okine", "Quartey", "Addo", "Lamptey",
    "Koomson", "Quaye", "Bruce", "Ankrah", "Tagoe", "Nortey", "Ashong",
    "Ablakwa", "Agbodza", "Amankwah", "Appiah", "Kusi", "Yeboah", "Kyei",
    "Ntim", "Okyere", "Kwarteng", "Donkor", "Asamoah", "Akufo", "Addai",
    "Bonsu", "Duah", "Wiredu", "Ampofo", "Baah", "Nyong", "Obeng"
]

UG_SCHOOLS_AND_PROGRAMS = {
    "College of Basic and Applied Sciences": [
        "Computer Science", "Information Technology", "Statistics", "Mathematics",
        "Physics", "Chemistry", "Biology", "Biochemistry", "Biotechnology",
        "Food Science and Nutrition", "Agricultural Science", "Animal Science"
    ],
    "College of Health Sciences": [
        "Medicine", "Nursing", "Pharmacy", "Dentistry", "Public Health",
        "Medical Laboratory Sciences", "Physiotherapy", "Radiography"
    ],
    "College of Humanities": [
        "English Language", "Linguistics", "French", "Philosophy", "Music",
        "Theatre Arts", "Fine Arts", "Dance Studies", "Religious Studies",
        "Arabic and Islamic Studies", "Modern Languages"
    ],
    "College of Education": [
        "Educational Administration", "Educational Psychology", "Curriculum Studies",
        "Educational Foundations", "Science Education", "Mathematics Education",
        "ICT Education", "Technical Education"
    ],
    "Legon Business School": [
        "Business Administration", "Accounting", "Finance", "Marketing",
        "Human Resource Management", "Supply Chain Management", "Entrepreneurship"
    ],
    "School of Law": ["Law"],
    "School of Social Sciences": [
        "Economics", "Political Science", "Sociology", "Geography", "History",
        "Psychology", "Social Work", "International Affairs", "African Studies"
    ]
}

# Comprehensive multi-school UG course catalog.
# ~140 courses spanning core disciplines + general education.
UG_COMPREHENSIVE_COURSES = [
    # Computer Science (existing detailed set retained)
    ("UGCS101", "Introduction to Computing", 3),
    ("UGCS102", "Programming Fundamentals", 3),
    ("UGCS201", "Data Structures and Algorithms", 3),
    ("UGCS202", "Computer Architecture", 3),
    ("UGCS301", "Database Systems", 3),
    ("UGCS302", "Software Engineering", 3),
    ("UGCS303", "Operating Systems", 3),
    ("UGCS401", "Computer Networks", 3),
    ("UGCS402", "Artificial Intelligence", 3),
    ("UGCS403", "Machine Learning", 3),
    # Information Technology
    ("UGIT201", "Web Development", 3),
    ("UGIT301", "Mobile App Development", 3),
    ("UGIT302", "Systems Analysis and Design", 3),
    ("UGIT401", "IT Project Management", 3),
    # Mathematics
    ("UGMA101", "Calculus I", 3),
    ("UGMA201", "Linear Algebra", 3),
    ("UGMA301", "Probability and Statistics", 3),
    ("UGMA401", "Numerical Methods", 3),
    # Physics
    ("UGPH101", "General Physics I", 3),
    ("UGPH201", "Electricity and Magnetism", 3),
    ("UGPH301", "Quantum Mechanics", 3),
    ("UGPH401", "Solid State Physics", 3),
    # Chemistry
    ("UGCH101", "General Chemistry I", 3),
    ("UGCH201", "Organic Chemistry", 3),
    ("UGCH301", "Physical Chemistry", 3),
    ("UGCH401", "Analytical Chemistry", 3),
    # Biology
    ("UGBI101", "General Biology I", 3),
    ("UGBI201", "Cell Biology", 3),
    ("UGBI301", "Genetics", 3),
    ("UGBI401", "Molecular Biology", 3),
    # Biotechnology
    ("UGBT101", "Intro to Biotechnology", 3),
    ("UGBT201", "Bioprocess Engineering", 3),
    ("UGBT301", "Genetic Engineering", 3),
    ("UGBT401", "Applied Biotechnology", 3),
    # Food Science / Nutrition
    ("UGFS101", "Intro Food Science", 3),
    ("UGFS201", "Food Microbiology", 3),
    ("UGFS301", "Food Processing Technology", 3),
    ("UGFS401", "Food Quality Assurance", 3),
    # Agricultural Science
    ("UGAG101", "Principles of Agriculture", 3),
    ("UGAG201", "Soil Science", 3),
    ("UGAG301", "Crop Production", 3),
    ("UGAG401", "Sustainable Agriculture", 3),
    # Animal Science
    ("UGAS101", "Intro Animal Science", 3),
    ("UGAS201", "Animal Nutrition", 3),
    ("UGAS301", "Livestock Production", 3),
    ("UGAS401", "Animal Health Management", 3),
    # Medicine
    ("UGMD101", "Human Anatomy I", 4),
    ("UGMD201", "Physiology", 4),
    ("UGMD301", "Pathology", 4),
    ("UGMD401", "Clinical Practice I", 4),
    # Nursing
    ("UGNS101", "Foundations of Nursing", 3),
    ("UGNS201", "Medical-Surgical Nursing", 3),
    ("UGNS301", "Community Health Nursing", 3),
    ("UGNS401", "Nursing Leadership", 3),
    # Pharmacy
    ("UGPHM101", "Intro Pharmaceutical Sciences", 3),
    ("UGPHM201", "Pharmacology I", 3),
    ("UGPHM301", "Medicinal Chemistry", 3),
    ("UGPHM401", "Clinical Pharmacy", 3),
    # Dentistry
    ("UGDS101", "Dental Anatomy", 3),
    ("UGDS201", "Oral Pathology", 3),
    ("UGDS301", "Restorative Dentistry", 3),
    ("UGDS401", "Oral Surgery", 3),
    # Public Health
    ("UGPHH101", "Intro Public Health", 3),
    ("UGPHH201", "Epidemiology", 3),
    ("UGPHH301", "Health Policy", 3),
    ("UGPHH401", "Global Health", 3),
    # Medical Laboratory Sciences
    ("UGMLS101", "Clinical Chemistry", 3),
    ("UGMLS201", "Hematology", 3),
    ("UGMLS301", "Medical Microbiology", 3),
    ("UGMLS401", "Diagnostic Techniques", 3),
    # Physiotherapy
    ("UGPT101", "Functional Anatomy", 3),
    ("UGPT201", "Therapeutic Exercise", 3),
    ("UGPT301", "Neurorehabilitation", 3),
    ("UGPT401", "Clinical Physiotherapy", 3),
    # Radiography
    ("UGRAD101", "Radiographic Physics", 3),
    ("UGRAD201", "Imaging Techniques", 3),
    ("UGRAD301", "Radiobiology", 3),
    ("UGRAD401", "Advanced Imaging", 3),
    # English Language
    ("UGENGL101", "Academic Writing", 3),
    ("UGENGL201", "Literary Analysis", 3),
    ("UGENGL301", "African Literature", 3),
    ("UGENGL401", "Contemporary World Literature", 3),
    # Linguistics
    ("UGLIN101", "Intro Linguistics", 3),
    ("UGLIN201", "Phonetics and Phonology", 3),
    ("UGLIN301", "Morphology and Syntax", 3),
    ("UGLIN401", "Sociolinguistics", 3),
    # French
    ("UGFRN101", "Basic French I", 3),
    ("UGFRN201", "Intermediate French", 3),
    ("UGFRN301", "Advanced French", 3),
    ("UGFRN401", "Francophone Studies", 3),
    # Philosophy
    ("UGPHIL101", "Intro Philosophy", 3),
    ("UGPHIL201", "Ethics", 3),
    ("UGPHIL301", "Metaphysics", 3),
    ("UGPHIL401", "Philosophy of Mind", 3),
    # Music
    ("UGMUS101", "Music Theory I", 3),
    ("UGMUS201", "Music Composition", 3),
    ("UGMUS301", "Ethnomusicology", 3),
    ("UGMUS401", "Music Production", 3),
    # Theatre Arts
    ("UGTHE101", "Intro Drama", 3),
    ("UGTHE201", "Acting Techniques", 3),
    ("UGTHE301", "Directing", 3),
    ("UGTHE401", "Playwriting", 3),
    # Fine Arts
    ("UGFAR101", "Foundations of Drawing", 3),
    ("UGFAR201", "Painting Techniques", 3),
    ("UGFAR301", "Sculpture", 3),
    ("UGFAR401", "Art Criticism", 3),
    # Dance Studies
    ("UGDAN101", "Dance Fundamentals", 3),
    ("UGDAN201", "African Dance Forms", 3),
    ("UGDAN301", "Choreography", 3),
    ("UGDAN401", "Performance Production", 3),
    # Religious Studies
    ("UGRST101", "World Religions", 3),
    ("UGRST201", "African Traditional Religion", 3),
    ("UGRST301", "Comparative Religion", 3),
    ("UGRST401", "Religion and Society", 3),
    # Arabic & Islamic Studies
    ("UGARB101", "Intro Arabic I", 3),
    ("UGARB201", "Intermediate Arabic", 3),
    ("UGARB301", "Classical Arabic Texts", 3),
    ("UGARB401", "Islamic Thought", 3),
    # Education (general)
    ("UGEDU101", "Foundations of Education", 3),
    ("UGEDU201", "Educational Psychology", 3),
    ("UGEDU301", "Curriculum Development", 3),
    ("UGEDU401", "Educational Leadership", 3),
    # Science Education
    ("UGSCI101", "Intro Science Education", 3),
    ("UGSCI201", "Teaching Science Methods", 3),
    ("UGSCI301", "Assessment in Science", 3),
    ("UGSCI401", "STEM Education Innovations", 3),
    # Mathematics Education
    ("UGMED101", "Math Teaching Methods", 3),
    ("UGMED201", "Instructional Design in Math", 3),
    ("UGMED301", "Assessment in Mathematics", 3),
    ("UGMED401", "Technology in Math Education", 3),
    # ICT Education
    ("UGTIC101", "ICT Literacy in Education", 3),
    ("UGTIC201", "Educational Technology Tools", 3),
    ("UGTIC301", "E-Learning Design", 3),
    ("UGTIC401", "ICT Policy in Education", 3),
    # Law
    ("UGLAW101", "Intro to Law", 3),
    ("UGLAW201", "Constitutional Law", 3),
    ("UGLAW301", "Criminal Law", 3),
    ("UGLAW401", "International Law", 3),
    # Economics
    ("UGECN101", "Principles of Economics", 3),
    ("UGECN201", "Microeconomics", 3),
    ("UGECN301", "Macroeconomics", 3),
    ("UGECN401", "Development Economics", 3),
    # Political Science
    ("UGPSC101", "Intro Political Science", 3),
    ("UGPSC201", "Comparative Politics", 3),
    ("UGPSC301", "International Relations", 3),
    ("UGPSC401", "Public Policy Analysis", 3),
    # Sociology
    ("UGSOC101", "Intro Sociology", 3),
    ("UGSOC201", "Social Theory", 3),
    ("UGSOC301", "Social Research Methods", 3),
    ("UGSOC401", "Sociology of Development", 3),
    # Geography
    ("UGGEO101", "Physical Geography", 3),
    ("UGGEO201", "Human Geography", 3),
    ("UGGEO301", "Geographic Information Systems", 3),
    ("UGGEO401", "Environmental Management", 3),
    # History
    ("UGHIS101", "African History I", 3),
    ("UGHIS201", "World History", 3),
    ("UGHIS301", "Colonialism and Independence", 3),
    ("UGHIS401", "Contemporary African Issues", 3),
    # Psychology
    ("UGPSY101", "Intro Psychology", 3),
    ("UGPSY201", "Developmental Psychology", 3),
    ("UGPSY301", "Cognitive Psychology", 3),
    ("UGPSY401", "Abnormal Psychology", 3),
    # Social Work
    ("UGSWK101", "Intro Social Work", 3),
    ("UGSWK201", "Human Behavior and Social Environment", 3),
    ("UGSWK301", "Social Welfare Policy", 3),
    ("UGSWK401", "Community Development", 3),
    # International Affairs
    ("UGINA101", "Foundations of Intl Affairs", 3),
    ("UGINA201", "Diplomacy", 3),
    ("UGINA301", "Conflict Resolution", 3),
    ("UGINA401", "Global Security", 3),
    # African Studies
    ("UGAFC101", "Intro African Studies", 3),
    ("UGAFC201", "African Cultures", 3),
    ("UGAFC301", "African Political Systems", 3),
    ("UGAFC401", "Pan-Africanism", 3),
    # Business Administration
    ("UGBUS101", "Intro Business Administration", 3),
    ("UGBUS201", "Organizational Behavior", 3),
    ("UGBUS301", "Business Strategy", 3),
    ("UGBUS401", "Corporate Governance", 3),
    # Accounting
    ("UGACC101", "Financial Accounting I", 3),
    ("UGACC201", "Management Accounting", 3),
    ("UGACC301", "Auditing", 3),
    ("UGACC401", "Advanced Financial Reporting", 3),
    # Finance
    ("UGFIN101", "Principles of Finance", 3),
    ("UGFIN201", "Corporate Finance", 3),
    ("UGFIN301", "Investment Analysis", 3),
    ("UGFIN401", "Financial Markets", 3),
    # Marketing
    ("UGMKT101", "Principles of Marketing", 3),
    ("UGMKT201", "Consumer Behavior", 3),
    ("UGMKT301", "Marketing Research", 3),
    ("UGMKT401", "Digital Marketing", 3),
    # Human Resource Management
    ("UGHRM101", "Intro Human Resource Management", 3),
    ("UGHRM201", "Recruitment and Selection", 3),
    ("UGHRM301", "Performance Management", 3),
    ("UGHRM401", "Strategic HRM", 3),
    # Supply Chain Management
    ("UGSUP101", "Intro Supply Chain", 3),
    ("UGSUP201", "Logistics Management", 3),
    ("UGSUP301", "Procurement Management", 3),
    ("UGSUP401", "Global Supply Networks", 3),
    # Entrepreneurship
    ("UGENT101", "Foundations of Entrepreneurship", 3),
    ("UGENT201", "New Venture Creation", 3),
    ("UGENT301", "Small Business Management", 3),
    ("UGENT401", "Innovation Management", 3),
    # General Education (picked as broad electives for selection logic)
    ("UGEN101", "Academic Writing and Communication", 3),
    ("UGEN102", "Critical Thinking", 3),
    ("UGEN201", "Ethics and Society", 3),
    ("UGEN202", "Research Methods", 3),
    ("UGEN301", "Entrepreneurship and Innovation", 3),
    ("UGEN302", "Leadership Development", 3),
    ("UGEN401", "Global Citizenship", 3),
    ("UGEN402", "Professional Practice Seminar", 3),
]

UG_ACADEMIC_CALENDAR = [
    ("1st Semester 2021/2022", "2021/2022", date(2021, 8, 16), date(2021, 12, 17)),
    ("2nd Semester 2021/2022", "2021/2022", date(2022, 1, 17), date(2022, 5, 20)),
    ("1st Semester 2022/2023", "2022/2023", date(2022, 8, 15), date(2022, 12, 16)),
    ("2nd Semester 2022/2023", "2022/2023", date(2023, 1, 16), date(2023, 5, 19)),
    ("1st Semester 2023/2024", "2023/2024", date(2023, 8, 14), date(2023, 12, 15)),
    ("2nd Semester 2023/2024", "2023/2024", date(2024, 1, 15), date(2024, 5, 17)),
    ("1st Semester 2024/2025", "2024/2025", date(2024, 8, 12), date(2024, 12, 13)),
    ("2nd Semester 2024/2025", "2024/2025", date(2025, 1, 13), date(2025, 5, 16))
]

__all__ = [
    "GHANAIAN_MALE_NAMES", "GHANAIAN_FEMALE_NAMES", "GHANAIAN_SURNAMES",
    "UG_SCHOOLS_AND_PROGRAMS", "UG_COMPREHENSIVE_COURSES", "UG_ACADEMIC_CALENDAR"
]
