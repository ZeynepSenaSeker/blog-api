# Blog API Documentation & Contract

This document specifies the REST API contract for the Blog service, including request parameters, payload shapes, authentication rules, and response wrappers.

---

## 1. Global Standards & Conventions

### Base URL
All API endpoints are served under `/api/`.

### Response Wrapper
Every endpoint returns a consistent JSON envelope:

#### Successful Response (`200 OK`, `201 Created`):
```json
{
  "success": true,
  "message": "Posts retrieved.",
  "data": { ... }
}
```

#### Error Response (`400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`):
```json
{
  "success": false,
  "message": "Please check the information you entered.",
  "errors": {
    "field_name": ["Specific validation error message."],
    "non_field_errors": ["General error message."]
  }
}
```

#### No Content (`204 No Content`):
Empty body with HTTP status 204.

---

## 2. Authentication & Authorization

Authentication is stateless and uses JSON Web Tokens (JWT).
When accessing protected endpoints, include the header:
```http
Authorization: Bearer <access_token>
```

| Header | Format | Lifetime |
|---|---|---|
| Access Token | `Bearer <token>` | 1 hour |
| Refresh Token | In request body | 7 days |

---

## 3. Endpoints Overview

### 🔐 Authentication

#### 1. Obtain Token Pair
* **Method:** `POST`
* **Path:** `/api/auth/token/`
* **Auth Required:** No
* **Request Body:**
  ```json
  {
    "username": "shali",
    "password": "yourpassword"
  }
  ```
* **Responses:**
  * `200 OK`: Returns `{"access": "<token>", "refresh": "<token>"}`
  * `401 Unauthorized`: Invalid credentials

#### 2. Refresh Access Token
* **Method:** `POST`
* **Path:** `/api/auth/token/refresh/`
* **Auth Required:** No
* **Request Body:**
  ```json
  {
    "refresh": "<refresh_token>"
  }
  ```
* **Responses:**
  * `200 OK`: Returns `{"access": "<token>"}`
  * `401 Unauthorized`: Invalid or expired refresh token

---

### 📂 Categories

#### 3. List Categories
* **Method:** `GET`
* **Path:** `/api/blog/categories/`
* **Auth Required:** No
* **Query Params:** None
* **Response `data`:**
  ```json
  [
    {
      "id": "e6f47774-c360-46f9-bc4c-35aa833758b9",
      "name": "Rehabilitation",
      "slug": "rehabilitation",
      "description": ""
    }
  ]
  ```

---

### 📝 Posts

#### 4. List Posts
* **Method:** `GET`
* **Path:** `/api/blog/posts/`
* **Auth Required:** No (Optional auth: when authenticated, includes own drafts)
* **Query Params:**
  * `category` (optional, string): Filter by category slug (e.g. `?category=rehabilitation`)
  * `search` (optional, string): Search in title and excerpt (e.g. `?search=knee`)
* **Response `data`:**
  ```json
  [
    {
      "id": "0dfeb750-68d7-463d-82d2-8dafbcfef960",
      "title": "Knee Rehabilitation Exercises After Surgery",
      "slug": "knee-rehabilitation-exercises-after-surgery",
      "excerpt": "A practical guide to knee rehabilitation exercises after surgery.",
      "cover_image_url": "",
      "cover_image_alt": "",
      "author": {
        "id": 1,
        "username": "demo_author",
        "full_name": "Demo Author"
      },
      "category": {
        "id": "e6f47774-c360-46f9-bc4c-35aa833758b9",
        "name": "Rehabilitation",
        "slug": "rehabilitation",
        "description": ""
      },
      "status": "published",
      "published_at": "2026-10-11T20:37:39+03:00",
      "reading_time_minutes": 1
    }
  ]
  ```

#### 5. Create Post
* **Method:** `POST`
* **Path:** `/api/blog/posts/`
* **Auth Required:** Yes (`IsAuthenticated`)
* **Request Body:**
  ```json
  {
    "title": "A Descriptive Article Title With 10+ Chars",
    "excerpt": "Short overview summary.",
    "content": "Full article body content with at least 100 words if published...",
    "cover_image_url": "https://example.com/image.jpg",
    "cover_image_alt": "Descriptive accessibility text",
    "meta_title": "SEO Title (≤ 70 chars)",
    "meta_description": "SEO description snippet (≤ 160 chars)",
    "focus_keyword": "target keyword phrase",
    "canonical_url": "",
    "is_indexable": true,
    "category_id": "e6f47774-c360-46f9-bc4c-35aa833758b9",
    "status": "draft"
  }
  ```
* **Validation Rules:**
  * `title`: Minimum 10 characters.
  * `meta_description`: Maximum 160 characters.
  * `content`: Minimum 100 words if `status == "published"`.
  * `slug`: Automatically generated uniquely on creation and never mutated upon updates.
  * `author`: Injected securely from authenticated session (`request.user`), client input ignored.
* **Responses:**
  * `201 Created`
  * `400 Bad Request` (Validation errors)
  * `401 Unauthorized`

#### 6. Get Post Detail
* **Method:** `GET`
* **Path:** `/api/blog/posts/<slug>/`
* **Auth Required:** No for published posts; Yes for unpublished drafts (author only)
* **Response `data`:**
  ```json
  {
    "id": "0dfeb750-68d7-463d-82d2-8dafbcfef960",
    "title": "Knee Rehabilitation Exercises After Surgery",
    "slug": "knee-rehabilitation-exercises-after-surgery",
    "excerpt": "A practical guide to knee rehabilitation exercises after surgery.",
    "content": "Recovery is a process, not an event...",
    "cover_image_url": "",
    "cover_image_alt": "",
    "seo_title": "Knee Rehabilitation Exercises After Surgery",
    "seo_description": "A practical guide to knee rehabilitation exercises after surgery.",
    "canonical_url": "",
    "is_indexable": true,
    "author": {
      "id": 1,
      "username": "demo_author",
      "full_name": "Demo Author"
    },
    "category": {
      "id": "e6f47774-c360-46f9-bc4c-35aa833758b9",
      "name": "Rehabilitation",
      "slug": "rehabilitation",
      "description": ""
    },
    "status": "published",
    "published_at": "2026-10-11T20:37:39+03:00",
    "updated_at": "2026-10-11T20:37:39+03:00",
    "reading_time_minutes": 1
  }
  ```
* **Responses:**
  * `200 OK`
  * `404 Not Found`

#### 7. Update Post (Partial / Full)
* **Method:** `PATCH` / `PUT`
* **Path:** `/api/blog/posts/<slug>/`
* **Auth Required:** Yes (Must be the author of the post)
* **Request Body:** Partial or complete subset of `PostWriteSerializer` fields.
* **Responses:**
  * `200 OK`
  * `400 Bad Request`
  * `401 Unauthorized`
  * `403 Forbidden` (`"You can only edit your own posts."`)
  * `404 Not Found`

#### 8. Delete Post
* **Method:** `DELETE`
* **Path:** `/api/blog/posts/<slug>/`
* **Auth Required:** Yes (Must be the author of the post)
* **Responses:**
  * `204 No Content`
  * `401 Unauthorized`
  * `403 Forbidden`
  * `404 Not Found`

#### 9. Publish Post (State Transition)
* **Method:** `POST`
* **Path:** `/api/blog/posts/<slug>/publish/`
* **Auth Required:** Yes (Must be the author of the post)
* **Request Body:** None
* **Responses:**
  * `200 OK`: Post successfully marked as `published`, `published_at` set to current time.
  * `401 Unauthorized`: Authentication required.
  * `403 Forbidden`: Authenticated user is not the post author.
  * `404 Not Found`: Post does not exist.
  * `409 Conflict`: Post is already published (`"This post is already published."`).

---

### 🌐 SEO Feed

#### 10. Sitemap Feed
* **Method:** `GET`
* **Path:** `/api/blog/sitemap/`
* **Auth Required:** No
* **Description:** Provides a lightweight feed of slugs and modification timestamps for every published and indexable article, powering `sitemap.xml`.
* **Response `data`:**
  ```json
  [
    {
      "slug": "knee-rehabilitation-exercises-after-surgery",
      "updated_at": "2026-10-11T20:37:39.901594+03:00"
    }
  ]
  ```

---

### 📖 Interactive Swagger Documentation
* **Swagger UI:** `/swagger/`
* Supports interactive request execution and Bearer token authorization.
