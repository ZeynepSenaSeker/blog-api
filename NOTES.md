# Week 1 — Engineering Notes

### 1. What is a migration, and why is it committed to git?
A migration is a version-controlled Python file that documents how the database schema changes over time when Django models are created or altered. Whenever models are modified, `makemigrations` creates a new migration file describing the diff, and `migrate` translates and applies those changes into actual SQL DDL against the database. Migrations are committed to git so that every developer and production environment can deterministically reproduce the exact same database structure. This guarantees team synchronization and prevents drift between application code and database schema across releases.

### 2. What is the N+1 problem, and how do you fix it?
The N+1 problem occurs when querying a set of records and subsequently executing an additional database query for every individual record in a loop (e.g., accessing a related foreign key attribute like `post.author.username`). For 100 posts, Django would fire 1 query to fetch the posts and 100 individual queries for each author, totaling 101 queries and causing major performance degradation. In Django, this is resolved by using `select_related()` for single-valued relationships (ForeignKey, OneToOne), which executes an SQL `JOIN` in a single query. For multi-valued relations (ManyToMany, reverse ForeignKeys), `prefetch_related()` is used, which executes a single additional query and stitches the results together in Python. In our tests, `select_related('author')` reduced query count from 5 down to 1.

### 3. Why UUID primary keys instead of 1, 2, 3?
Sequential auto-incrementing integer IDs leak sensitive business intelligence to users and competitors by exposing the total volume and creation velocity of records (e.g., seeing `/posts/42/` reveals that only 42 posts exist). Furthermore, sequential IDs make scraping and enumeration attacks trivial because an attacker can iterate through consecutive numbers to harvest every record. UUIDv4 keys are globally unique, 128-bit cryptographically random identifiers that prevent enumeration and data exposure. They also allow records to be generated safely in distributed environments or client-side before being written to the database without ID collisions.

### 4. CASCADE vs SET_NULL — when would you pick each?
`CASCADE` and `SET_NULL` are foreign key deletion rules that encode architectural domain decisions directly into the database schema. `CASCADE` is used when a child record's lifecycle is strictly dependent on the parent; if a user is deleted, their personal draft and authored posts should typically be deleted alongside them. Conversely, `SET_NULL` (which requires `null=True`) is selected when the child record should survive the parent's deletion; if a topic category is deleted, the blog posts should remain accessible with their category field set to null rather than being wiped out. Choosing between them is a deliberate product decision regarding data ownership and preservation.

### 5. Which fields on Post exist purely for SEO, and what does each one do?
The `Post` model contains several dedicated SEO fields:
- `slug`: Serves as the human-readable, keyword-rich URL path; once published, it must never change to preserve inbound backlinks and search rankings.
- `meta_title`: Populates the HTML `<title>` tag and the blue clickable headline in search engine result pages (~60–70 characters), falling back to the post title.
- `meta_description`: Generates the summary snippet shown beneath the title in search engine result pages (~160–170 characters), falling back to the excerpt.
- `focus_keyword`: Stores the primary keyword phrase the article targets for editorial tracking and on-page optimization.
- `cover_image_alt`: Provides accessible descriptive text for screen readers and assists search engine image indexing.
- `canonical_url`: Specifies the authoritative original source URL when content is republished from elsewhere, preventing duplicate-content ranking penalties.
- `is_indexable`: Emits a `noindex` robots meta directive when unchecked, allowing content to remain published without search engines indexing it.
