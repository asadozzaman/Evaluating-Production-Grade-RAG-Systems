# CLEAR-RAG System — Complete Non-Technical User Guide

**System Name:** CLEAR-RAG (Comprehensive Large Language Model Evaluation Assessment for RAG Systems)  
**Guide Version:** 1.0  
**Audience:** Non-technical users, first-time users, team members, evaluators, and managers  

---

## WHAT IS CLEAR-RAG?

CLEAR-RAG is a web-based system that helps teams test and measure the quality of AI assistants. When an AI assistant answers a question, it usually searches a set of documents first (this is called "retrieval"), then generates an answer. CLEAR-RAG helps you check: Did the AI find the right documents? Did it give a correct and helpful answer? Is it ready for real use?

You do not need any programming knowledge to use this system. This guide explains every feature step by step.

---

## TABLE OF CONTENTS

1. Login and Registration Guide
2. Dashboard Guide
3. Project Creation Guide
4. Source Documents Guide (Upload & URI)
5. Document Indexing Guide
6. Test Questions Guide
7. Question Dataset Import Guide
8. Evaluation Run Creation Guide
9. RAG Execution Guide (Running the AI)
10. CLEAR-RAG Scoring Guide (Manual Scoring)
11. Error Taxonomy Guide (Tagging Mistakes)
12. Automated Evaluation Guide (LLM-as-Judge)
13. Evaluation Review Guide (Approving Scores)
14. Batch Experiment Guide
15. Run Comparison Guide
16. Experiment Leaderboard Guide
17. Production Readiness Guide
18. Report Builder Guide
19. Export Guide (CSV and JSON)
20. Background Jobs Guide
21. Audit Trail and Governance Guide
22. Edit and Update Guide
23. Delete Guide
24. Error Message Guide
25. Common User Mistakes Guide
26. Full Start-to-Finish Workflow Example

---

---

# FEATURE 1: LOGIN AND REGISTRATION

--------------------------------------------------
## Feature Name: User Registration and Login
--------------------------------------------------

### 1. Purpose of This Feature

This feature allows you to create a personal account in CLEAR-RAG and sign in to the system. Without an account, you cannot access any part of the system.

- **What it does:** Creates a secure personal account linked to your email address.
- **Why you need it:** The system protects all project data and only allows authorized users to view or change information.
- **When to use it:** The very first time you open CLEAR-RAG, you must register. Every time after that, you log in with your email and password.
- **What problem it solves:** Keeps your evaluation data private and ensures only team members can access it.

---

### 2. Before You Start

Before registering, you need:
- A valid email address that you have access to
- A password you will remember (minimum 8 characters)
- The web address (URL) of the CLEAR-RAG system provided by your system administrator

**Important note about roles:**
- The very **first person** who registers in the system automatically becomes the **Admin** (the most powerful role — can do everything).
- Every person who registers **after** the first user becomes a **Viewer** (read-only access — can see data but cannot create or change anything).
- An Admin can later upgrade a Viewer to an **Evaluator** (can create projects, run evaluations, and score answers).

---

### 3. Where to Find This Feature

1. Open your web browser (Chrome, Firefox, Edge, etc.).
2. Type the CLEAR-RAG website address in the address bar and press Enter.
3. You will land on the **Landing Page** (home page).
4. Click **"Get started"** to register, or **"Sign in"** if you already have an account.

---

### 4. Step-by-Step Use

**REGISTRATION (Creating a New Account)**

**Step 1: Open the registration page**  
From the landing page, click the **"Get started"** button. The registration form will open. You will see a form on the right side of the screen and a brand panel on the left showing sample system metrics.

**Step 2: Enter your full name**  
In the **"Full name"** field, type your first and last name.  
- Example: `asadozzaman`  
- This name will appear on your account and in the system's activity records.

**Step 3: Enter your email address**  
In the **"Email address"** field, type your work email.  
- Example: `asadozzaman@company.com`  
- This email is your username. You will use it every time you log in.  
- Use an email you check regularly, as it identifies you in the system.

**Step 4: Enter a password**  
In the **"Password"** field, type a password.  
- The password must be at least **8 characters** long.  
- Example: `Evaluation2024!`  
- Choose something secure — do not use your name or the word "password."

**Step 5: Click "Create account"**  
After filling in all three fields, click the **"Create account"** button at the bottom of the form.

**Step 6: Wait for confirmation**  
The system will check your details. If everything is correct, you will be taken directly to the **Dashboard** page. You are now logged in.

---

**LOGIN (Signing In to an Existing Account)**

**Step 1: Open the login page**  
From the landing page, click **"Sign in"**. The login form will open.

**Step 2: Enter your email address**  
In the **"Email address"** field, type the email you registered with.

**Step 3: Enter your password**  
In the **"Password"** field, type your password.

**Step 4: Click "Sign in"**  
Click the **"Sign in"** button. The system checks your email and password. If correct, you are taken to the Dashboard.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Full name | Your first and last name | Identifies you in the system | Sarah Johnson |
| Email address | Your work email address | Used as your login username | sarah@company.com |
| Password | A password of 8+ characters | Secures your account | Evaluation2024! |

---

### 6. What Happens After Saving

After clicking "Create account" or "Sign in":
- The system checks that your details are correct.
- A secure login token is created for your session.
- You are redirected to the main **Dashboard** page.
- Your name and role (Admin, Evaluator, or Viewer) appear on the dashboard.

---

### 7. Output After This Step

**Output Name:** Dashboard Page  
**What the user will see:** The main control center of the system with your name displayed, your role badge, and navigation options.  
**What it means:** You are now logged in and ready to use the system.  
**Why it is useful:** You can now access projects, create evaluations, and view reports.

---

### 8. Example Scenario

A user named "faysalahmed" is joining the CLEAR-RAG team for the first time.

1. James opens the CLEAR-RAG website.
2. He clicks "Get started."
3. He enters: Full name = `faysal`, Email = `faysal@company.com`, Password = `SecurePass123!`.
4. He clicks "Create account."
5. Since five other people already registered before him, James becomes a **Viewer**.
6. James sees the Dashboard and can browse projects, but cannot create or change anything.
7. Later, the Admin promotes James to **Evaluator**, and James can now score evaluations.

---

### 9. Common Mistakes

**Mistake 1: Using a password shorter than 8 characters**  
Why this is a problem: The system will reject the password and not create the account.  
How to fix: Use a password with at least 8 characters, mixing letters, numbers, and symbols.

**Mistake 2: Entering the wrong email at login**  
Why this is a problem: The system cannot find your account and will show an error.  
How to fix: Double-check your email spelling before clicking "Sign in."

**Mistake 3: Forgetting your password**  
Why this is a problem: You cannot log in.  
How to fix: Contact your system administrator to reset your password. (Self-service password reset needs confirmation of availability in your version.)

---

### 10. Simple Summary

This feature lets you create your account and log in. The first person to register becomes Admin. Everyone else starts as a Viewer until promoted. After logging in, you land on the Dashboard and can begin working.

---

---

# FEATURE 2: DASHBOARD

--------------------------------------------------
## Feature Name: Main Dashboard
--------------------------------------------------

### 1. Purpose of This Feature

The Dashboard is the central home page of CLEAR-RAG. From here, you can navigate to all parts of the system, see your account details, and quickly reach your projects.

- **What it does:** Gives you an overview and quick access to everything in the system.
- **Why you need it:** Instead of guessing where to go, the dashboard shows you exactly what to do next.
- **When to use it:** Every time you log in, you start here.
- **What problem it solves:** Saves time by providing one central navigation point.

---

### 2. Before You Start

You must be logged in. The dashboard requires a valid account.

---

### 3. Where to Find This Feature

After logging in, you are automatically taken to the Dashboard. If you are already inside the system and want to return to the dashboard:
1. Look at the top navigation bar.
2. Click **"Dashboard"** in the navigation menu.

---

### 4. Step-by-Step Use

**Step 1: Look at the welcome area**  
At the top of the dashboard, you will see a welcome message with your name. This confirms you are logged in as the correct user.

**Step 2: Check your account card**  
Your account card shows:
- Your full name
- Your email address
- Your role (Admin, Evaluator, or Viewer) shown as a colored badge

**Step 3: Use the Quick Actions**  
The dashboard has two main quick-action buttons:
- **"Browse Projects"** — Click this to see all existing projects in the system.
- **"New project"** — Click this to start creating a brand new project.

**Step 4: Navigate using the top menu**  
The navigation bar at the top of every page always shows:
- **Dashboard** — Returns you to this home page.
- **Projects** — Shows the full list of all projects.

---

### 5. What Happens After Opening the Dashboard

- The system loads your account information.
- Your role and permissions are confirmed.
- You can now click any button to go to the area you need.

---

### 6. Simple Summary

The Dashboard is your starting point. It shows your name and role, and gives you two quick ways to start: browse existing projects or create a new one. You return here anytime by clicking "Dashboard" in the top navigation.

---

---

# FEATURE 3: PROJECT CREATION

--------------------------------------------------
## Feature Name: Creating a New Project
--------------------------------------------------

### 1. Purpose of This Feature

A **Project** is the main workspace in CLEAR-RAG. Everything you do — uploading documents, creating test questions, running evaluations — happens inside a project.

- **What it does:** Creates a new, separate workspace for evaluating one AI system or one RAG use case.
- **Why you need it:** Each AI system being tested should have its own project so results do not mix.
- **When to use it:** When you want to start evaluating a new AI assistant, chatbot, or knowledge system.
- **What problem it solves:** Organizes all your evaluation work in one place, separated from other projects.

---

### 2. Before You Start

Before creating a project, you need:
- An **Admin** or **Evaluator** account (Viewers cannot create projects).
- A clear idea of what system you are evaluating (e.g., "Internal HR chatbot" or "Customer support bot").
- The intended users of that system (e.g., "HR team staff" or "customers").

---

### 3. Where to Find This Feature

1. Log in to CLEAR-RAG.
2. From the Dashboard, click **"New project"** or click **"Browse Projects"** then click **"New project"** in the top-right corner.
3. You will be taken to the **Create Project** form page.

---

### 4. Step-by-Step Use

**Step 1: Open the Create Project page**  
Click the **"New project"** button. A form appears with four fields to fill in.

**Step 2: Enter the Project Name**  
Click in the **"Project name"** field and type a clear, descriptive name for this project.
- This name will appear in all project lists, reports, and leaderboards.
- Choose a name that describes the AI system being tested.
- Example: `HR Knowledge Assistant Evaluation Q1 2025`

**Step 3: Select the System Type**  
Click the **"System type"** dropdown and select the type that best describes your AI system. Available options are:
- `internal_knowledge_assistant` — An AI that answers questions from internal company documents
- `customer_support_bot` — An AI that handles customer service questions
- `document_qa` — An AI that answers questions from specific documents
- `code_assistant` — An AI that helps with programming and code
- `research_tool` — An AI that helps with research and literature
- `other` — Any other type not listed above

Why this matters: The system type helps organize and categorize your projects. Select the option that most closely matches your AI system.

**Step 4: Enter the Target Users**  
Click in the **"Target users"** field and type who uses the AI system being evaluated.
- Example: `HR department staff and managers`
- Example: `Customer service agents`
- Example: `Medical researchers`

This information appears as a badge on the project card and helps your team quickly understand the purpose of the project.

**Step 5: Enter a Description (Optional)**  
Click in the **"Description"** field and write a brief explanation of the project's goal.
- This is optional but recommended.
- Example: `Evaluating the RAG system used by the HR department to answer policy-related questions. Testing question coverage, answer accuracy, and citation quality.`

**Step 6: Review all fields before submitting**  
Before clicking the button, re-read your entries:
- Is the project name clear and specific?
- Is the system type correct?
- Did you describe who uses the system?

**Step 7: Click "Create project"**  
Click the **"Create project"** button at the bottom of the form.

**Step 8: Wait for confirmation**  
The system saves the project. You are automatically taken to the **Project Setup Page** for your new project.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Project name | A clear name for this evaluation project | Identifies the project in all lists and reports | HR Knowledge Assistant Evaluation Q1 2025 |
| System type | Select the AI system category from dropdown | Categorizes and organizes projects | internal_knowledge_assistant |
| Target users | Who uses the AI system being tested | Helps team understand project context | HR department staff and managers |
| Description | Brief explanation of what is being tested | Provides context for team members | Evaluating HR policy chatbot for accuracy |

---

### 6. What Happens After Saving

After clicking "Create project":
- The project is saved in the database with a unique ID.
- You are redirected to the Project Setup Page.
- The project now appears in the Projects list.
- The project is empty — it has no documents, questions, or runs yet. You must add those next.
- The project is linked to your user account as the creator.

---

### 7. Output After This Step

**Output Name:** Project Setup Page  
**What the user will see:** A page with your project name at the top and multiple empty sections: Source Documents, Test Questions, Question Datasets, Batch Experiment, Leaderboard, Run Comparison, and Audit Trail.  
**What it means:** Your project workspace is ready. All sections are currently empty and waiting for you to add data.  
**Why it is useful:** You now have a dedicated space where all evaluation work for this AI system will be organized.

---

### 8. Example Scenario

A team wants to evaluate their company's internal HR chatbot.

1. The evaluator logs in and clicks "New project."
2. She enters: Project name = `HR Chatbot Evaluation 2025`, System type = `internal_knowledge_assistant`, Target users = `HR team and employees`, Description = `Testing the accuracy of our HR policy question-answering system.`
3. She clicks "Create project."
4. The system saves the project and opens the Project Setup Page.
5. The new project now appears in the Projects list for all team members to see.
6. The evaluator can now start adding documents and questions to this project.

---

### 9. Common Mistakes

**Mistake 1: Leaving the Project Name too vague**  
Why this is a problem: A name like "Test Project 1" tells nobody what the project is about.  
How to fix: Use a name that includes the system name and evaluation period, like "Customer Support Bot — March 2025 Evaluation."

**Mistake 2: Selecting the wrong System Type**  
Why this is a problem: The system type appears on all project cards and affects how the team understands the project.  
How to fix: If unsure, choose `other` and write a detailed description.

**Mistake 3: Creating duplicate projects**  
Why this is a problem: Team members may enter data into the wrong project.  
How to fix: Before creating a new project, check the Projects list to make sure a similar project does not already exist.

---

### 10. Simple Summary

A Project is the container for everything in CLEAR-RAG. Creating a project requires a name, system type, and target users. After saving, the project appears in the Projects list and a dedicated workspace is created, ready for you to add documents, questions, and evaluation runs.

---

---

# FEATURE 4: SOURCE DOCUMENTS

--------------------------------------------------
## Feature Name: Adding Source Documents (Upload or URI)
--------------------------------------------------

### 1. Purpose of This Feature

Source documents are the knowledge base — the files and documents that the AI system uses to answer questions. Adding them to CLEAR-RAG allows the system to search them and measure how well the AI retrieves relevant information.

- **What it does:** Stores documents (PDFs, Word files, text files, etc.) or document links in the project so the AI can search them during evaluation.
- **Why you need it:** Without source documents, there is nothing for the AI to search and no way to measure retrieval quality.
- **When to use it:** After creating a project, before running any evaluations.
- **What problem it solves:** Provides the knowledge base that mirrors what the real AI system uses, allowing accurate testing.

---

### 2. Before You Start

Before adding documents, you need:
- An existing project to add documents to (Admin or Evaluator role required).
- The actual document files in one of these formats: `.pdf`, `.docx`, `.txt`, `.csv`, or `.md`
- OR the URI (web address or link) of the document if linking rather than uploading.
- A clear title and type description for each document.

---

### 3. Where to Find This Feature

1. Log in and go to the **Projects** list.
2. Click on your project name to open the **Project Setup Page**.
3. Scroll down to find the **"Source Documents"** section (shows a count badge, e.g., "3 documents").
4. Click the section header to expand it if it is collapsed.

---

### 4. Step-by-Step Use

**METHOD A: Uploading a File**

**Step 1: Open the Source Documents section**  
On the Project Setup Page, find the "Source Documents" section. You will see a mini-list of existing documents (empty if none added yet) and an "Add document" or upload button.

**Step 2: Open the upload form**  
Click the button to open the document upload form. A panel or modal will appear with input fields.

**Step 3: Enter the Document Title**  
In the **"Title"** field, type a name that describes this document.
- Be specific and descriptive.
- Example: `HR Leave Policy 2024`
- Example: `Product Returns FAQ`

**Step 4: Enter the Document Type**  
In the **"Document type"** field, type a short label describing the category of this document.
- Example: `policy`
- Example: `faq`
- Example: `manual`
- Example: `report`

This label appears as a badge next to the document and helps you distinguish between different types of sources.

**Step 5: Enter the Version (Optional)**  
In the **"Version"** field, type a version identifier if this document has versions.
- Example: `v2.1`
- Example: `2024-Q1`
- Leave blank if not applicable.

**Step 6: Select the file to upload**  
Click the **"File"** input field (or the "Choose file" / "Browse" button). A file browser opens.
- Navigate to where your document is saved on your computer.
- Select the file.
- Accepted file types: `.pdf`, `.docx`, `.txt`, `.csv`, `.md`
- The file name will appear next to the button once selected.

**Step 7: Click "Upload document"**  
Click the **"Upload document"** button. The file is sent to the server.

**Step 8: Wait for the upload to complete**  
Larger files take a moment to upload. The system shows a loading indicator. Do not close the page while uploading.

**Step 9: Check the document appears in the list**  
After upload, the document appears in the Source Documents list showing its title and document_type badge.

---

**METHOD B: Adding a URI (Document Link)**

Use this method when your document is hosted online or on a shared server, and you want to link to it rather than upload a copy.

**Step 1 to Step 4:** Same as above — open the form, enter Title, Document Type, Version.

**Step 5: Enter the URI**  
Instead of uploading a file, enter the **URI** (the web address or file path) of the document.
- Example: `https://company.sharepoint.com/documents/hr-policy.pdf`
- Example: `s3://my-bucket/documents/faq.pdf`

**Step 6: Click "Add document"**  
The document link is saved. Note: URI-based documents cannot be indexed for vector search (only uploaded files can be indexed).

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Title | A clear, descriptive name for the document | Identifies the document in all lists | HR Leave Policy 2024 |
| Document type | Category label for this document | Helps organize and filter documents | policy |
| Version | Version number or date identifier | Tracks document versions | v2.1 |
| File | The actual document file from your computer | The AI will search this document | leave_policy.pdf |
| URI | Web address of the document (if not uploading) | Links to an externally hosted document | https://company.com/docs/policy.pdf |

---

### 6. What Happens After Saving

After the document is uploaded or linked:
- The file is stored securely on the server in a folder organized by project.
- The document appears in the Source Documents list with its title and type badge.
- The document is now available for the AI to search during evaluation runs.
- If you uploaded a file, you can click **"Index"** to prepare it for vector (semantic) search.
- The document count badge on the section header increases.

---

### 7. Output After This Step

**Output Name:** Source Documents List Entry  
**What the user will see:** A row in the Source Documents list showing: document title, document_type badge (e.g., "policy" in blue), and an "Index" button (for uploaded files).  
**What it means:** The document is now part of this project's knowledge base.  
**Why it is useful:** The AI can now search this document when answering test questions during evaluation.

---

### 8. Example Scenario

An evaluator is setting up a project for an internal knowledge assistant. The AI uses three documents: an HR Leave Policy PDF, an Employee Benefits guide, and a Remote Work Policy.

1. The evaluator opens the project and finds the Source Documents section.
2. She clicks "Add document" and fills in: Title = `HR Leave Policy 2024`, Type = `policy`, and selects the file `leave_policy_2024.pdf`.
3. She clicks "Upload document." The file uploads successfully.
4. She repeats for the other two documents.
5. All three documents now appear in the Source Documents list.
6. She clicks "Index" on each document to prepare them for vector search.

---

### 9. Common Mistakes

**Mistake 1: Uploading the wrong version of a document**  
Why this is a problem: The AI will search an outdated document and answers will not reflect current information.  
How to fix: Always check the file name and version before uploading. Use the Version field to track which version is loaded.

**Mistake 2: Using a very vague document title**  
Why this is a problem: When you have 10+ documents, a title like "Document 1" or "PDF" is impossible to identify.  
How to fix: Write a clear title like "Remote Work Policy 2024 — Version 3."

**Mistake 3: Uploading an unsupported file type**  
Why this is a problem: The system only accepts `.pdf`, `.docx`, `.txt`, `.csv`, `.md`. Other file types will be rejected.  
How to fix: Convert your document to a supported format before uploading. For example, convert `.doc` to `.docx` or a scanned image to a text-based PDF.

**Mistake 4: Adding too many irrelevant documents**  
Why this is a problem: Including documents unrelated to the AI system will skew retrieval metrics.  
How to fix: Only add the documents that the actual AI system uses as its knowledge base.

---

### 10. Simple Summary

Source Documents are the knowledge base that the AI searches. You can either upload files (PDF, DOCX, TXT, CSV, MD) or link to external documents using a URI. After adding, documents appear in the list and can be indexed for better vector search. Always use clear titles and correct document types to keep things organized.

---

---

# FEATURE 5: DOCUMENT INDEXING

--------------------------------------------------
## Feature Name: Indexing a Document for Vector Search
--------------------------------------------------

### 1. Purpose of This Feature

Indexing converts a document's text into a special mathematical format (called "embeddings" or "vectors") that the AI can use to find relevant paragraphs by meaning — not just keywords.

- **What it does:** Reads the uploaded document, breaks it into sections (chunks), and generates a numerical representation of each chunk so the AI can search by meaning.
- **Why you need it:** Without indexing, the AI can only do keyword matching (finding exact words). With indexing, the AI can find relevant content even when the exact words do not match.
- **When to use it:** After uploading a document and before running evaluations with **Vector** retrieval mode.
- **What problem it solves:** Enables smarter, meaning-based document search rather than simple word matching.

---

### 2. Before You Start

Before indexing a document, you need:
- The document must already be uploaded (not URI-based — only uploaded files can be indexed).
- An active Gemini API connection (configured by your system administrator).
- Admin or Evaluator role.

---

### 3. Where to Find This Feature

1. Go to your project's **Source Documents** section.
2. Find the document you want to index in the list.
3. Look for the **"Index"** button next to the document.

---

### 4. Step-by-Step Use

**Step 1: Find the document in the Source Documents list**  
On the Project Setup Page, scroll to the Source Documents section. Find the document you want to index.

**Step 2: Click the "Index" button**  
Next to the document, click the **"Index"** button. This begins the indexing process.

**Step 3: Wait for indexing to complete**  
Indexing may take several seconds to a few minutes depending on document size. The system processes the document:
- It extracts the full text from the file.
- It breaks the text into smaller sections called "chunks."
- It sends each chunk to the AI (Gemini) to generate embeddings.
- It stores the embeddings in the database.

Do not close the page while indexing is running.

**Step 4: Check for confirmation**  
After indexing is complete, the system saves the chunks. You can verify by clicking "View chunks" or looking at the chunk count if shown.

---

### 5. What Happens After Indexing

- The document's text is split into chunks stored in the Document Chunks table.
- Each chunk has an embedding (a list of numbers representing its meaning).
- When you run evaluations with Vector retrieval mode, the system uses these embeddings to find the most relevant chunks for each question.
- The document is now fully ready for both keyword and vector retrieval.

---

### 6. Simple Summary

Indexing prepares a document for smart, meaning-based search. Click the "Index" button next to any uploaded document. Wait for it to finish. Then the system can find relevant sections even when the exact question words are not in the document. You must index before using Vector retrieval mode.

---

---

# FEATURE 6: TEST QUESTIONS

--------------------------------------------------
## Feature Name: Creating Test Questions
--------------------------------------------------

### 1. Purpose of This Feature

Test questions are the questions you want the AI system to answer. They are the core of every evaluation. For each question, the AI will search documents, generate an answer, and then you (or the automated judge) will score how good the answer was.

- **What it does:** Creates individual test questions that the AI will be asked during evaluation.
- **Why you need it:** Without questions, there is nothing to evaluate. Questions define what you are testing.
- **When to use it:** After adding source documents, before creating evaluation runs.
- **What problem it solves:** Defines the test cases for the evaluation in a structured, repeatable way.

---

### 2. Before You Start

Before adding questions, you need:
- An existing project (Admin or Evaluator role).
- A list of questions you want to test the AI on.
- Knowledge of what document or section each question should be answered from (optional but helpful).

---

### 3. Where to Find This Feature

1. Open your project's **Project Setup Page**.
2. Scroll to the **"Test Questions"** section (shows a count badge).
3. Click to expand and see the question list and "Add question" button.

---

### 4. Step-by-Step Use

**Step 1: Open the Test Questions section**  
Find the "Test Questions" section on your Project Setup Page. Click to expand it. You will see a list of existing questions (empty if none yet) and an "Add question" button.

**Step 2: Click "Add question"**  
Click the **"Add question"** button. A form appears with fields to fill in.

**Step 3: Enter the Question Text**  
In the **"Question text"** field, type the complete question you want the AI to answer.
- Write it as a real question a user would ask.
- Be specific and clear.
- Example: `What is the maximum number of annual leave days an employee can carry over to the next year?`
- Example: `How do I submit a remote work request?`

**Step 4: Select the Question Type**  
Click the **"Question type"** dropdown and select the type that best describes this question. Options:
- `simple_factual` — A straightforward question with a single factual answer. Example: "What is the company's maternity leave policy?"
- `conditional` — A question where the answer depends on a condition. Example: "If an employee has worked for 3 years, how many days of leave do they get?"
- `multi_document` — A question that requires combining information from multiple documents. Example: "How does the remote work policy interact with the leave policy during public holidays?"
- `ambiguous` — A question that could be interpreted in multiple ways. Example: "Can I work from home?"
- `edge_case` — An unusual or boundary question that tests the limits of the AI. Example: "What happens to my leave days if the company closes for a month?"

Select the type that best matches your question. This helps analyze which types of questions the AI handles well or poorly.

**Step 5: Enter the Expected Source (Optional)**  
In the **"Expected source"** field, type the name of the document or section where the correct answer can be found.
- This is optional but very important for measuring retrieval quality.
- Example: `HR Leave Policy 2024`
- Example: `Remote Work Policy — Section 3`

When you enter this, the system will check whether the AI retrieved content from the correct source. If it did not, retrieval quality scores will be lower.

**Step 6: Click "Add question"**  
Click the **"Add question"** button to save the question.

**Step 7: Verify the question appears in the list**  
The question should now appear in the Test Questions list, showing the question text and a color-coded badge for its type.

**Step 8: Repeat for all questions**  
Add as many questions as needed. You can also import large sets of questions from a file (see Feature 7: Question Dataset Import).

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Question text | The full question to ask the AI | Defines what the AI must answer | What is the maximum carry-over leave days? |
| Question type | Category of the question (dropdown) | Helps analyze AI performance by type | simple_factual |
| Expected source | Document name where answer should come from | Used to measure retrieval accuracy | HR Leave Policy 2024 |

---

### 6. What Happens After Saving

After clicking "Add question":
- The question is saved to the database linked to this project.
- The question appears in the Test Questions list with its type badge.
- The question count badge on the section header increases.
- This question is now available to include in evaluation runs.
- When the AI runs, it will be asked this exact question.

---

### 7. Example Scenario

An evaluator wants to test whether the HR chatbot correctly answers three leave-related questions.

1. She opens the project and finds Test Questions section.
2. She clicks "Add question."
3. Question 1: Text = `How many sick leave days are employees entitled to per year?`, Type = `simple_factual`, Expected source = `HR Leave Policy 2024`.
4. She saves it and repeats for two more questions.
5. All three questions are now listed and ready for evaluation.

---

### 9. Common Mistakes

**Mistake 1: Writing a question that is too vague**  
Why this is a problem: "Tell me about leave" is not a clear test case and the AI cannot be fairly scored on it.  
How to fix: Write specific, answerable questions like "How many annual leave days does a full-time employee get?"

**Mistake 2: Forgetting to set Expected Source**  
Why this is a problem: The system cannot measure whether the AI retrieved from the correct document, so retrieval hit rate will always be 0%.  
How to fix: Always enter the document name in "Expected source" unless the question truly spans multiple documents.

**Mistake 3: Selecting the wrong Question Type**  
Why this is a problem: The analysis of which question types the AI struggles with will be inaccurate.  
How to fix: Review the type options carefully before selecting. When in doubt, use `simple_factual` for straightforward questions.

---

### 10. Simple Summary

Test questions are the questions you want the AI to answer. Add them one by one using the "Add question" form, or import large sets from a file. Always include the expected source document to enable accurate retrieval scoring. Questions are the foundation of every evaluation run.

---

---

# FEATURE 7: QUESTION DATASET IMPORT

--------------------------------------------------
## Feature Name: Importing Question Datasets from CSV or JSON Files
--------------------------------------------------

### 1. Purpose of This Feature

Instead of creating questions one by one, you can import a large set of questions at once from a file. This is useful when you have dozens or hundreds of questions prepared in a spreadsheet or file.

- **What it does:** Reads a CSV or JSON file containing many questions and adds them all to the project at once.
- **Why you need it:** Creating 50+ questions manually would be very time-consuming.
- **When to use it:** When you have a prepared test dataset — a file of questions already organized.
- **What problem it solves:** Saves time and enables consistent, standardized test datasets that can be reused across evaluations.

---

### 2. Before You Start

Before importing, you need:
- An existing project (Admin or Evaluator role).
- A CSV or JSON file with your questions, formatted correctly.
- CSV files must include these column headers: `question_text`, `question_type`, `expected_source`
- JSON files should follow the same structure.

**CSV Format Example:**
```
question_text,question_type,expected_source
How many annual leave days do employees get?,simple_factual,HR Leave Policy 2024
What is the remote work approval process?,conditional,Remote Work Policy
```

---

### 3. Where to Find This Feature

1. Open your project's **Project Setup Page**.
2. Scroll to the **"Question Datasets"** section.
3. Expand the section to see the import form.

---

### 4. Step-by-Step Use

**Step 1: Prepare your CSV or JSON file**  
Before coming to the system, prepare your file on your computer:
- Open a spreadsheet program (Excel, Google Sheets).
- Create columns: `question_text`, `question_type`, `expected_source`.
- Fill in your questions row by row.
- Save as `.csv` (Comma-separated values) format.

**Step 2: Open the Question Datasets section**  
On the Project Setup Page, find the "Question Datasets" section and expand it.

**Step 3: Enter Dataset Name**  
In the **"Dataset name"** field, type a name for this set of questions.
- Example: `HR Policy Test Dataset — January 2025`
- Choose a name that identifies when and why this dataset was created.

**Step 4: Enter Dataset Version (Optional)**  
In the **"Dataset version"** field, type a version identifier.
- Example: `v1.0`
- Example: `2025-01`
- This helps you track which version of a dataset was used in each experiment.

**Step 5: Select the file to import**  
Click the file input field and browse to your CSV or JSON file. Select it.

**Step 6: Click "Import"**  
Click the **"Import"** button. The system reads the file, validates it, and creates all questions.

**Step 7: Wait for import to complete**  
The system processes each row. This may take a moment for large files.

**Step 8: Check the dataset appears in the list**  
After import, the dataset appears in the Question Datasets list showing: dataset name, question count, and version. All questions from the file are now available in this project.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Dataset name | Name for this question set | Identifies this dataset in lists | HR Policy Test Dataset — January 2025 |
| Dataset version | Version label for the dataset | Tracks which version was used | v1.0 |
| File | The CSV or JSON question file | Contains all questions to import | hr_questions_jan2025.csv |

---

### 6. What Happens After Importing

After clicking "Import":
- The system reads every row in the file.
- Each row becomes a test question linked to this project.
- A new dataset record is created showing the dataset name, version, and count.
- All imported questions now appear in the Test Questions list.
- The Question Datasets section shows the dataset as a card with question count.
- The dataset can be selected later when setting up Batch Experiments.

---

### 7. Common Mistakes

**Mistake 1: Wrong column headers in the CSV file**  
Why this is a problem: If the CSV columns are not named exactly `question_text`, `question_type`, `expected_source`, the import will fail.  
How to fix: Double-check column headers match exactly before importing.

**Mistake 2: Invalid question_type values in the CSV**  
Why this is a problem: The system only accepts these exact values: `simple_factual`, `conditional`, `multi_document`, `ambiguous`, `edge_case`.  
How to fix: Check every row uses one of these exact values.

**Mistake 3: Importing the same dataset twice**  
Why this is a problem: This creates duplicate questions and inflates question counts.  
How to fix: Check the Question Datasets list before importing. If the dataset already exists, do not import again.

---

### 10. Simple Summary

Question Dataset Import lets you add many test questions at once from a CSV or JSON file. Prepare your file with the correct column headers, enter a dataset name and version, then click Import. All questions are added instantly and the dataset appears in the list for use in Batch Experiments.

---

---

# FEATURE 8: EVALUATION RUN CREATION

--------------------------------------------------
## Feature Name: Creating an Evaluation Run
--------------------------------------------------

### 1. Purpose of This Feature

An Evaluation Run is a single experiment where the AI is tested against your questions. Each run uses specific settings (which model to use, how to retrieve documents) and produces a set of scores and metrics.

- **What it does:** Creates a new experiment that will run the AI on your test questions and collect results.
- **Why you need it:** You can run multiple experiments with different settings and compare which configuration performs best.
- **When to use it:** After setting up documents and questions, when you are ready to run the AI and collect results.
- **What problem it solves:** Organizes results by experiment so you can compare different AI configurations side by side.

---

### 2. Before You Start

Before creating a run, you need:
- At least one source document added to the project.
- At least one test question added (or a dataset imported).
- Admin or Evaluator role.

---

### 3. Where to Find Evaluation Runs

Evaluation runs are created through the Batch Experiment feature (Feature 14) or individually:
1. Open your project's **Project Setup Page**.
2. Scroll to the **Experiment Leaderboard** section to see existing runs.
3. Runs are created when you run a Batch Experiment (see Feature 14).

---

### 4. What Is in an Evaluation Run Record

Each run contains:
- **Run Name:** A label you give this experiment (e.g., "Vector Search — Gemini Flash — v1.0")
- **System Version:** A version label for the AI system being tested (e.g., "v1.2.0")
- **Retrieval Mode:** Whether the system uses keyword search or vector (semantic) search
- **Generator Model:** The AI model that generates answers (e.g., "gemini-2.5-flash")
- **Embedding Model:** The model used to create document embeddings (for vector search)
- **Judge Model:** The model used to automatically score answers
- **Status:** Current state of the run (pending / running / completed / failed)
- **Notes:** Optional notes about the experiment setup

---

### 5. Simple Summary

Evaluation runs are individual experiments. Each run tests your AI system's questions and records all retrieved chunks, generated answers, and scores. Multiple runs can be created with different settings and compared using the Leaderboard and Run Comparison features. Runs are most easily created through the Batch Experiment form.

---

---

# FEATURE 9: RAG EXECUTION (RUNNING THE AI)

--------------------------------------------------
## Feature Name: Running the AI (RAG Execution with Gemini)
--------------------------------------------------

### 1. Purpose of This Feature

This feature makes the AI actually answer your test questions. "RAG Execution" means the system:
1. Takes a question.
2. Searches your documents for relevant sections.
3. Sends those sections plus the question to the Gemini AI model.
4. Collects the AI's answer.
5. Saves both the retrieved document sections and the generated answer for scoring.

- **What it does:** Runs the full AI pipeline — retrieval + answer generation — for one or all questions.
- **Why you need it:** You cannot evaluate an AI system without first making it produce answers to score.
- **When to use it:** After setting up documents, questions, and a run — when you are ready to see the AI's answers.
- **What problem it solves:** Automates the process of getting AI answers so you can focus on evaluating quality.

---

### 2. Before You Start

Before running the AI, you need:
- An existing evaluation run open.
- Source documents added and indexed (for vector search) or just added (for keyword search).
- Test questions added to the project.
- Gemini API key configured by your system administrator.
- Admin or Evaluator role.

---

### 3. Where to Find This Feature

1. Open your project and click on an evaluation run name (from the Leaderboard section or by navigating to the run).
2. You are now on the **Run Evaluation Page**.
3. Look for the **"Question & Outputs"** section.

---

### 4. Step-by-Step Use

**Step 1: Open the Run Evaluation Page**  
Navigate to an evaluation run. The page shows the run name at the top, its status badge, and several expandable sections.

**Step 2: Find the Question & Outputs section**  
Expand the **"Question & Outputs"** section. You will see a question selector dropdown.

**Step 3: Select a question (for single-question execution)**  
Click the question selector dropdown. A list of all project questions appears. Select the question you want the AI to answer.
- After selecting, any previously retrieved chunks and answers for this question will appear.

**Step 4: Select Retrieval Mode**  
Before clicking "Run Gemini RAG," select how you want the AI to search documents:
- **Keyword** — Finds documents containing the exact words from the question. Faster and simpler.
- **Vector** — Finds documents based on meaning similarity. Smarter but requires documents to be indexed first.

**Step 5: Click "Run Gemini RAG"**  
Click the **"Run Gemini RAG"** button. The system begins the full retrieval and generation pipeline.

**Step 6: Wait for the process to complete**  
The AI pipeline runs in several stages:
1. Extracts text from source documents.
2. Searches for relevant document sections (chunks).
3. Ranks the chunks by relevance.
4. Sends the question and top chunks to Gemini.
5. Collects and saves the AI's answer.

This may take 10–60 seconds per question. Wait until the process finishes.

**Step 7: Review the Retrieved Chunks**  
After completion, scroll down to the **Retrieved Chunks** list. You will see:
- The document sections the AI found for this question.
- Each chunk shows: rank (1 = most relevant), the chunk text, the relevance label badge (high/medium/low/irrelevant), and retrieval time in milliseconds.

**Step 8: Review the Generated Answer**  
Below the chunks, find the **Generated Answers** section. You will see:
- The AI's answer to the question.
- The model name used (e.g., "gemini-2.5-flash").
- Token count (how many words the AI processed).
- Generation time in milliseconds.
- Estimated cost in dollars.

**Step 9: Check if the answer is useful**  
Read the generated answer. Does it actually answer the question? Is it based on the retrieved document sections? This is what you will score in the next step.

---

### 5. What Happens After Execution

After the AI runs:
- Retrieved chunks are saved and linked to this question and run.
- The generated answer is saved and linked to this question and run.
- These outputs are now ready for scoring (Feature 10: CLEAR-RAG Scoring).
- The run's status updates to reflect progress.
- Cost and timing data are recorded for performance analysis.

---

### 6. Output After This Step

**Output Name:** Retrieved Chunks and Generated Answer  

**Retrieved Chunks:**  
What you will see: A numbered list of document sections the AI found. Each section shows the rank (1 = most relevant), the text, a color badge showing relevance (green=high, yellow=medium, orange=low, red=irrelevant), and how long retrieval took.  
What it means: These are the pieces of your documents that the AI read before writing its answer.  

**Generated Answer:**  
What you will see: The full text of the AI's answer, plus the model name, how many words were processed (tokens), how long it took, and the cost.  
What it means: This is the AI's actual response. You will score how accurate, complete, and faithful this answer is.

---

### 7. Example Scenario

An evaluator wants to see how the HR chatbot answers: "How many days of sick leave does an employee get per year?"

1. She opens the evaluation run and expands Question & Outputs.
2. She selects the sick leave question from the dropdown.
3. She selects "Vector" retrieval mode (documents are indexed).
4. She clicks "Run Gemini RAG."
5. After 15 seconds, the system shows 3 retrieved chunks from the "HR Leave Policy 2024" document.
6. The generated answer says: "Full-time employees are entitled to 10 days of sick leave per year, as outlined in the HR Leave Policy."
7. The evaluator can now see exactly what information the AI used and what it said.
8. She proceeds to score this answer in the CLEAR-RAG Scoring section.

---

### 9. Common Mistakes

**Mistake 1: Trying vector search before indexing documents**  
Why this is a problem: Vector search requires document embeddings. Without indexing, it cannot find anything.  
How to fix: Index all documents first using the "Index" button in Source Documents, then use Vector mode.

**Mistake 2: Not waiting for the execution to finish before leaving the page**  
Why this is a problem: The process may not complete, leaving partial or missing results.  
How to fix: Wait for the success message or check that retrieved chunks and an answer appear before navigating away.

**Mistake 3: Running the same question multiple times**  
Why this is a problem: This creates multiple answers and chunks for one question, which may confuse the scoring.  
How to fix: Check if a question already has results before clicking "Run Gemini RAG" again.

---

### 10. Simple Summary

"Run Gemini RAG" makes the AI search your documents and write an answer for each test question. Select a question, choose keyword or vector retrieval, then click the button. The AI returns retrieved document sections and a generated answer. These results are then ready to be scored in the CLEAR-RAG Scoring section.

---

---

# FEATURE 10: CLEAR-RAG SCORING (MANUAL SCORING)

--------------------------------------------------
## Feature Name: Scoring Answers with the CLEAR-RAG Framework
--------------------------------------------------

### 1. Purpose of This Feature

CLEAR-RAG Scoring is how you measure the quality of the AI's answers. You review each answer and give it a score from 1 to 5 across five different dimensions. These five scores are automatically averaged into one overall quality score.

The five dimensions are:
- **C — Citation Quality:** Did the AI properly cite or reference the source documents?
- **L — Latency and Cost:** Was the answer generated quickly and efficiently?
- **E — Evidence Faithfulness:** Does the answer only contain information that was in the retrieved documents?
- **A — Answer Relevance:** Does the answer actually address the question asked?
- **R — Retrieval Quality:** Did the system retrieve the most relevant document sections?

- **What it does:** Captures structured quality ratings for each AI-generated answer.
- **Why you need it:** Numbers and scores make quality measurable and comparable across experiments.
- **When to use it:** After the AI has generated answers, you (or the automated judge) score each one.
- **What problem it solves:** Turns subjective "is this good?" into objective, comparable, trackable scores.

---

### 2. Before You Start

Before scoring, you need:
- An evaluation run with at least one generated answer (AI must have run first).
- Admin or Evaluator role.
- Familiarity with the 1–5 scoring scale (1 = very poor, 5 = excellent).
- Time to carefully read both the question, the retrieved chunks, and the generated answer.

---

### 3. Where to Find This Feature

1. Open an evaluation run page.
2. In the **"Question & Outputs"** section, select a question from the dropdown.
3. The **"CLEAR-RAG Scoring"** form appears below the generated answer.

---

### 4. Step-by-Step Use

**Step 1: Select the question to score**  
From the question dropdown, select a question. The retrieved chunks and generated answer for this question appear on the page.

**Step 2: Read the question**  
Read the question carefully. Understand exactly what information the user was looking for.

**Step 3: Read the retrieved chunks**  
Review all the document sections the AI retrieved. Ask yourself:
- Are these chunks from the right document?
- Do they contain the information needed to answer the question?

**Step 4: Read the generated answer**  
Read the AI's full answer carefully. Compare it against:
- The question (does it answer what was asked?)
- The retrieved chunks (is the answer based on the documents?)

**Step 5: Score Citation Quality (1-5)**  
In the **"Citation Quality Score"** dropdown, select a score from 1 to 5.

Scoring guide:
- **5 (Excellent):** The AI clearly mentioned where its information came from, referencing the correct document and section.
- **4 (Good):** The AI referenced sources but slightly imprecisely.
- **3 (Acceptable):** Partial citation — some information referenced, some not.
- **2 (Poor):** Minimal or incorrect citations.
- **1 (Very Poor):** No citation at all, or cited the wrong source entirely.

**Step 6: Score Latency and Cost Efficiency (1-5)**  
In the **"Latency and Cost Efficiency Score"** dropdown, select a score.

Scoring guide:
- **5 (Excellent):** Answer generated very quickly, minimal tokens used.
- **4 (Good):** Fast with reasonable token usage.
- **3 (Acceptable):** Acceptable speed and cost.
- **2 (Poor):** Slow or expensive compared to the value of the answer.
- **1 (Very Poor):** Unacceptably slow or costly.

*Note: You can see the generation time (in milliseconds) and token counts in the Generated Answer section to help with this score.*

**Step 7: Score Evidence Faithfulness (1-5)**  
In the **"Evidence Faithfulness Score"** dropdown, select a score.

Scoring guide:
- **5 (Excellent):** Every claim in the answer can be found in the retrieved chunks. No made-up information.
- **4 (Good):** Almost entirely faithful, minor unsupported details.
- **3 (Acceptable):** Mostly faithful but includes some information not from the documents.
- **2 (Poor):** Significant content not supported by evidence.
- **1 (Very Poor):** The answer contains major hallucinations — information that is not in any document.

*This is the most important dimension. An AI that makes up facts ("hallucinates") is dangerous.*

**Step 8: Score Answer Relevance (1-5)**  
In the **"Answer Relevance Score"** dropdown, select a score.

Scoring guide:
- **5 (Excellent):** The answer directly and completely addresses the question.
- **4 (Good):** Mostly on-topic with minor irrelevant content.
- **3 (Acceptable):** Partially answers the question.
- **2 (Poor):** Mostly off-topic or only tangentially related.
- **1 (Very Poor):** The answer does not address the question at all.

**Step 9: Score Retrieval Quality (1-5)**  
In the **"Retrieval Quality Score"** dropdown, select a score.

Scoring guide:
- **5 (Excellent):** The system retrieved exactly the right document sections in the top results.
- **4 (Good):** Mostly relevant chunks retrieved with minor irrelevant ones.
- **3 (Acceptable):** Some relevant chunks but mixed with irrelevant ones.
- **2 (Poor):** Mostly irrelevant chunks. The system found the wrong sections.
- **1 (Very Poor):** Completely wrong chunks retrieved. The system failed to find any relevant information.

**Step 10: Enter Reviewer Notes (Optional)**  
In the **"Reviewer notes"** text area, write any observations about this answer.
- Example: `The AI correctly cited the leave policy but missed the special clause for part-time employees.`
- Example: `Answer is excellent. Directly answers the question with correct figures.`

**Step 11: Enter Suggested Improvement (Optional)**  
In the **"Suggested improvement"** text area, write a recommendation.
- Example: `System should index Section 4 more specifically to capture the part-time employee exception.`

**Step 12: Click "Score answer"**  
Click the **"Score answer"** button. The five scores are saved.

**Step 13: Check the overall score**  
The system automatically calculates the **Overall Score** as the average of all five dimension scores. For example:
- Citation Quality: 4
- Latency and Cost: 5
- Evidence Faithfulness: 3
- Answer Relevance: 4
- Retrieval Quality: 3
- **Overall Score = (4+5+3+4+3) / 5 = 3.8**

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Citation Quality Score | Score 1-5 for source citation quality | Measures if AI cited sources correctly | 4 |
| Latency and Cost Efficiency Score | Score 1-5 for speed and efficiency | Measures if AI was fast and cost-effective | 5 |
| Evidence Faithfulness Score | Score 1-5 for factual accuracy | Measures if AI only said what's in the documents | 3 |
| Answer Relevance Score | Score 1-5 for how well it answers the question | Measures if AI answered the right thing | 4 |
| Retrieval Quality Score | Score 1-5 for document retrieval accuracy | Measures if the right chunks were found | 3 |
| Reviewer notes | Optional text explaining your scoring | Provides context for the scores | Answer missed the part-time exception |
| Suggested improvement | Optional text for how to improve | Captures actionable feedback | Index Section 4 more specifically |

---

### 6. What Happens After Scoring

After clicking "Score answer":
- All five scores and the auto-calculated overall score are saved.
- The evaluation mode is set to "human."
- The review status is set to "pending_review" (waiting for a reviewer to approve).
- Scores appear in the Evaluation Summary Analytics panel.
- The run's average scores update in the leaderboard.

---

### 7. Output After This Step

**Output Name:** Evaluation Record with Scores  
**What the user will see:** The five individual scores and the calculated overall score appear in the evaluation summary. Dimension averages update in the analytics panel.  
**What it means:** You have formally measured the quality of this AI answer.  
**Why it is useful:** These scores enable comparison across questions, runs, and experiments. They drive the leaderboard ranking and production readiness gates.

---

### 8. Example Scenario

An evaluator is scoring the AI's answer to: "How many sick leave days does an employee get?"

The AI answered: "Employees receive 10 sick leave days per year per the HR Leave Policy."

The evaluator reads the retrieved chunk: It is from the HR Leave Policy 2024, Section 2, and says exactly "Full-time employees are entitled to 10 sick leave days annually."

Scoring:
- Citation Quality: 4 (AI referenced policy but did not specify section number)
- Latency and Cost: 5 (answered in 1.2 seconds, low token count)
- Evidence Faithfulness: 5 (answer is exactly what the document says, no made-up content)
- Answer Relevance: 5 (directly answers the question)
- Retrieval Quality: 5 (correct document section was retrieved)
- **Overall Score: 4.8**

---

### 9. Common Mistakes

**Mistake 1: Scoring without reading the retrieved chunks**  
Why this is a problem: You cannot properly score Evidence Faithfulness or Retrieval Quality without checking what the AI actually retrieved.  
How to fix: Always read the retrieved chunks before scoring. Compare the answer against them.

**Mistake 2: Being inconsistent with scores across different questions**  
Why this is a problem: A score of "3 for Evidence Faithfulness" should mean the same thing for every answer. Inconsistency makes averages meaningless.  
How to fix: Refer to the scoring guide above and apply it consistently.

**Mistake 3: Clicking "Score answer" before reviewing all five dimensions**  
Why this is a problem: A score of 1 left by accident will lower the overall average significantly.  
How to fix: Review all five dropdowns before clicking save.

---

### 10. Simple Summary

CLEAR-RAG Scoring is how you formally rate each AI answer. Give a score from 1 to 5 for each of the five CLEAR dimensions. The system calculates the overall score automatically. These scores drive the leaderboard, production readiness gates, and comparison reports. Always read both the retrieved chunks and the answer before scoring.

---

---

# FEATURE 11: ERROR TAXONOMY (TAGGING MISTAKES)

--------------------------------------------------
## Feature Name: Adding Error Tags to AI Answers
--------------------------------------------------

### 1. Purpose of This Feature

Sometimes an AI answer has a specific type of problem — it hallucinated a fact, missed a key document, or gave an incomplete response. The Error Taxonomy feature lets you tag exactly what type of error occurred and how serious it is.

- **What it does:** Adds a structured error label to a specific AI answer, categorizing the type and severity of the problem.
- **Why you need it:** Scoring tells you HOW good an answer is. Error tagging tells you WHY it was bad and what specifically went wrong.
- **When to use it:** When reviewing an AI answer that has a specific, identifiable problem.
- **What problem it solves:** Builds a categorized record of all AI errors so teams can see patterns and prioritize improvements.

---

### 2. Before You Start

- An evaluation run with at least one generated answer.
- Admin or Evaluator role.
- A clear understanding of what went wrong with the answer.

---

### 3. Where to Find This Feature

1. Open an evaluation run page.
2. In the Question & Outputs section, select a question.
3. Below the generated answer, find the **"Error Taxonomy"** section.
4. Click **"Add error tag"** to open the form.

---

### 4. Step-by-Step Use

**Step 1: Identify the problem with the answer**  
Before tagging, clearly identify what went wrong. Read the question, chunks, and answer carefully.

**Step 2: Open the Error Taxonomy section**  
Find and expand the Error Taxonomy section. Click "Add error tag."

**Step 3: Select the Error Category**  
Click the **"Category"** dropdown and select the type of error:

- `retrieval_miss` — The system failed to retrieve the relevant document section. The answer may be correct but unsupported because the right chunks were not found.
- `citation_error` — The AI cited a source incorrectly — wrong document, wrong section, or made-up reference.
- `hallucination` — **Most serious.** The AI stated a fact that is NOT in any document. It invented information.
- `incomplete_answer` — The answer is partially correct but missing important information.
- `irrelevant_answer` — The answer does not address the question at all.
- `contradiction` — The answer contradicts information in the retrieved documents.
- `latency_cost` — The answer took too long or cost too much to generate.
- `format_error` — The answer is in the wrong format (e.g., should be a list but is a paragraph).
- `policy_ambiguity` — The answer could not be determined because the source document is itself unclear or contradictory.
- `other` — Any problem that does not fit the above categories.

**Step 4: Select the Severity**  
Click the **"Severity"** dropdown and select how serious this error is:
- `low` — Minor issue, does not significantly affect usefulness.
- `medium` — Noticeable problem, reduces answer quality.
- `high` — Significant problem, answer is partially wrong or misleading.
- `critical` — The answer is dangerously wrong, contains major false information, or could mislead users seriously.

**Important:** Any answer tagged as `high` or `critical` severity will **block** the Production Readiness gate. The run cannot be approved for production if blocking errors exist.

**Step 5: Add Notes (Optional)**  
In the **"Notes"** field, describe the error in your own words.
- Example: `AI stated employees get 15 sick days. The policy says 10. This is a hallucination.`

**Step 6: Add Evidence Reference (Optional)**  
In the **"Evidence reference"** field, paste the actual correct text from the document that proves the error.
- Example: `From HR Leave Policy 2024, Section 2: "Full-time employees are entitled to 10 sick leave days annually."`

**Step 7: Click "Add error tag"**  
Click the button to save the error tag.

**Step 8: Check the Error Taxonomy panel**  
At the run level, there is an **Error Taxonomy** aggregation panel that shows a summary of all errors by category and severity across all questions. This gives you a "health report" of the AI system.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Category | Type of error from dropdown | Classifies what went wrong | hallucination |
| Severity | How serious the error is | Determines if it blocks production | critical |
| Notes | Your description of the error | Provides context for the team | AI said 15 days, policy says 10 |
| Evidence reference | The correct text from documents | Proves the error with evidence | Section 2: "10 sick leave days annually" |

---

### 6. What Happens After Saving

After saving an error tag:
- The error is recorded and linked to the specific answer, question, and run.
- The Error Taxonomy summary panel updates with error counts by category and severity.
- If the error is `high` or `critical` severity, the Production Readiness gate for "blocking errors" will show a FAIL status.
- The leaderboard score for this run is penalized for errors.

---

### 7. Simple Summary

Error tags let you record exactly what went wrong with a specific AI answer. Select the error type (hallucination, retrieval miss, etc.) and severity (low to critical). High and critical errors block the run from being approved for production. Use the Error Taxonomy panel to see a summary of all errors across the run.

---

---

# FEATURE 12: AUTOMATED EVALUATION (LLM-AS-JUDGE)

--------------------------------------------------
## Feature Name: Automated Evaluation Using AI Judge
--------------------------------------------------

### 1. Purpose of This Feature

Instead of manually scoring every answer yourself, you can ask another AI model (the "judge") to score the answers automatically using the same CLEAR-RAG five-dimension framework.

- **What it does:** Uses a Gemini AI model to automatically review each answer and assign CLEAR-RAG scores.
- **Why you need it:** Manual scoring of hundreds of answers is very time-consuming. Automated scoring is fast.
- **When to use it:** When you want quick initial scores across all questions, or when running large batch experiments.
- **What problem it solves:** Dramatically reduces the time needed to complete initial evaluations. Human reviewers can then focus on reviewing and approving (or overriding) automated scores.

---

### 2. Before You Start

- Evaluation run with generated answers.
- Gemini API key configured (by system administrator).
- Admin or Evaluator role.

---

### 3. Where to Find This Feature

**Method 1 — Directly from the run page:**
1. Open an evaluation run page.
2. Scroll to the **"Background Jobs"** section.
3. Click **"Queue Auto-Evaluation"**.

**Method 2 — In Batch Experiment:**  
When setting up a Batch Experiment (Feature 14), you can enable **"auto_evaluate"** so evaluation runs automatically after RAG execution.

---

### 4. Step-by-Step Use

**Step 1: Open the Background Jobs section on the run page**  
Find the "Background Jobs" panel on the evaluation run page.

**Step 2: Click "Queue Auto-Evaluation"**  
Click this button. A background job is created and queued.

**Step 3: Wait for the job to complete**  
The job appears in the Background Jobs list with its status:
- `queued` — Job is waiting to start.
- `running` — Job is currently processing.
- `completed` — Job finished successfully.
- `failed` — Job encountered an error.

Click **"Refresh"** to update the job status. Large runs may take several minutes.

**Step 4: Check the automated scores**  
After the job completes, automated scores appear in:
- The Evaluation Summary Analytics panel (dimension averages update).
- The Question Results table (each question now shows scores with "automated" badge).
- The Evaluation Review panel (items appear with judge reasoning text).

**Step 5: Review the judge's reasoning**  
For each automated score, the judge provides a brief reasoning text explaining why it gave each score. You will find this in the **Evaluation Review** panel under "judge reasoning."

---

### 5. What Happens After Automated Evaluation

- Each AI answer receives five scores (one per CLEAR dimension) from the judge.
- Scores are marked with evaluation_mode = "automated."
- Review status is set to "pending_review."
- A human evaluator must now review these automated scores (Feature 13) and either approve them or override them.
- Judge calibration metrics become available (comparing automated scores to human scores when both exist).

---

### 6. Simple Summary

Automated Evaluation runs a Gemini AI model as a judge to score all AI answers automatically. Queue it from the Background Jobs panel, wait for it to complete, then review the automated scores in the Evaluation Review panel. A human must still review and approve (or override) the judge's scores before a run can pass production readiness.

---

---

# FEATURE 13: EVALUATION REVIEW (APPROVING SCORES)

--------------------------------------------------
## Feature Name: Review and Approve Evaluation Scores
--------------------------------------------------

### 1. Purpose of This Feature

The Evaluation Review feature is the "human-in-the-loop" quality control step. After automated scoring (or manual scoring), a reviewer must check each score and either approve it or mark it for revision.

- **What it does:** Lets a reviewer check each question's answer and scores, then approve or override them.
- **Why you need it:** Human judgment catches mistakes that automated scoring may miss. Approval is required before a run passes production readiness.
- **When to use it:** After automated evaluation has run, or after manual scoring is complete.
- **What problem it solves:** Ensures a human validates AI-generated scores before they influence production decisions.

---

### 2. Before You Start

- At least one scored evaluation (manual or automated).
- Admin or Evaluator role.

---

### 3. Where to Find This Feature

1. Open an evaluation run page.
2. Scroll to the **"Evaluation Review"** section.

---

### 4. Step-by-Step Use

**Step 1: Open the Evaluation Review panel**  
Find and expand the Evaluation Review section. You will see:
- Counts at the top: Pending / Approved / Needs Revision
- A list of review items — one per question that has been scored.

**Step 2: Read the question**  
For each review item, read the question text at the top.

**Step 3: Read the retrieved chunks**  
Check which document sections were retrieved for this question.

**Step 4: Read the generated answer**  
Read the AI's full answer.

**Step 5: Read the current scores**  
Check the five dimension scores already assigned (by the AI judge or a human evaluator). The judge reasoning text explains why these scores were given.

**Step 6: Decide: Approve or needs revision?**

**If the scores look correct:**
- Select **"approved"** in the Review Status.
- Click **"Save review"**.
- The evaluation is marked as approved.

**If the scores need adjustment:**
- Select **"needs_revision"** in the Review Status.
- Optionally override individual scores: Enter new values (1-5) for any dimension score you disagree with.
- Enter **"Review notes"** explaining why you are overriding (e.g., "Evidence Faithfulness should be 2, not 4 — the AI included unverified data.").
- Enter **"Score change reason"** (e.g., "AI judge overestimated faithfulness. Manually corrected.").
- Click **"Save review"**.

**Step 7: Repeat for all items**  
Work through all pending review items. The Pending count decreases and Approved count increases as you work.

**Step 8: Check review completion**  
In the Evaluation Summary Analytics panel, check the **"Reviewed"** count and **"Completion %"**. The run passes the "human review" production gate only when completion reaches 100%.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Review status | approved / needs_revision / pending_review | Records the human decision | approved |
| Score overrides (optional) | New score 1-5 for any dimension | Corrects inaccurate automated scores | Evidence Faithfulness: 2 |
| Review notes | Explanation for the review decision | Documents why scores were changed | AI judge overestimated faithfulness |
| Score change reason | Reason for score override | Provides audit trail for changes | Manual check found unsupported claim |

---

### 6. What Happens After Review

- The review status is updated (approved, needs_revision).
- If scores were overridden, the new scores replace the old ones.
- The reviewer's user ID and timestamp are recorded.
- Review completion percentage updates.
- When all evaluations are approved, the "human_review_complete" production gate passes.
- All changes are recorded in the Audit Trail.

---

### 7. Simple Summary

The Evaluation Review panel shows every question's scores waiting for human approval. Read each question, answer, and chunk carefully, then approve the scores or override them if incorrect. Full review completion (100%) is required before a run can pass the production readiness check.

---

---

# FEATURE 14: BATCH EXPERIMENT

--------------------------------------------------
## Feature Name: Running a Batch Experiment
--------------------------------------------------

### 1. Purpose of This Feature

A Batch Experiment runs the entire evaluation process automatically for all questions in a dataset at once — RAG execution, and optionally automated scoring — creating a complete evaluation run with a single click.

- **What it does:** Runs the AI on every question in a dataset, collects all answers, and optionally scores them automatically.
- **Why you need it:** Running individual questions one by one would take hours. Batch experiments complete the entire process in minutes.
- **When to use it:** When you want to run a full evaluation of your AI system against a complete test dataset.
- **What problem it solves:** Automates the time-consuming task of running the AI on dozens or hundreds of questions.

---

### 2. Before You Start

Before running a Batch Experiment, you need:
- A question dataset imported (see Feature 7).
- Source documents uploaded (and indexed for vector retrieval).
- Admin or Evaluator role.
- Gemini API key configured.

---

### 3. Where to Find This Feature

1. Open your project's **Project Setup Page**.
2. Scroll down to the **"Batch Experiment"** section.
3. Expand the section to see the batch experiment form.

---

### 4. Step-by-Step Use

**Step 1: Open the Batch Experiment section**  
On the Project Setup Page, expand the Batch Experiment section. A form with several fields appears.

**Step 2: Enter a Run Name**  
In the **"Run name"** field, type a descriptive name for this experiment.
- Be specific — this name appears in the Leaderboard and comparison views.
- Example: `Vector Search — Gemini Flash — HR Dataset v1.0`
- Example: `Keyword Search — Baseline — January 2025`

The run name should capture the key settings so you can identify it later.

**Step 3: Select the Question Dataset**  
Click the **"Dataset"** dropdown and select the question dataset to use.
- All imported question datasets for this project appear here.
- Select the dataset whose questions you want to run in this experiment.

**Step 4: Select Source Documents**  
In the **"Document IDs"** multi-select area, check the boxes next to the documents you want the AI to search.
- You can select one or multiple documents.
- Only select documents relevant to the questions in the dataset.
- Example: If your dataset has HR questions, select only HR-related documents.

**Step 5: Select Retrieval Mode**  
Choose how the AI should search the documents:
- **Keyword** — Searches for exact word matches. Works without indexing.
- **Vector** — Searches by meaning. Requires documents to be indexed first.

To compare both modes, run two separate experiments — one with keyword, one with vector.

**Step 6: Enter System Version (Optional)**  
In the **"System version"** field, enter a version identifier for the AI system being tested.
- Example: `v1.2.0`
- Example: `pre-release-march-2025`
- This helps track which version of the system you were testing.

**Step 7: Enter Notes (Optional)**  
In the **"Notes"** field, write any important context about this experiment.
- Example: `Testing with updated HR documents after March revision.`

**Step 8: Enable/Disable Auto-Evaluate**  
If available, toggle the **"Auto-evaluate"** option:
- **ON:** After RAG execution, the system automatically scores all answers using the AI judge. Saves time but requires human review afterward.
- **OFF:** Only RAG execution runs; scoring must be done manually or triggered separately.

**Step 9: Click "Run Batch Experiment"**  
Click the **"Run Batch Experiment"** button. The system creates the evaluation run and begins processing.

**Step 10: Monitor progress**  
The section shows a status update. You can also check the **Background Jobs** panel for the job's current step and status. The steps typically are:
1. Creating the run
2. Running RAG for question 1 of N
3. Running RAG for question 2 of N
4. ... (repeats for every question)
5. Running auto-evaluation (if enabled)
6. Generating summary
7. Completed

**Step 11: Review the completed run**  
When complete, a summary message shows total questions processed, answers generated, and average scores (if auto-evaluate was on). Click "Open run" to view the full results.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Run name | Descriptive name for this experiment | Identifies the run in lists and leaderboard | Vector Search — Gemini Flash — HR Dataset v1.0 |
| Dataset | Select question dataset | Determines which questions the AI answers | HR Policy Test Dataset — January 2025 |
| Document IDs | Select source documents to search | Defines the AI's knowledge base for this run | HR Leave Policy 2024, Remote Work Policy |
| Retrieval mode | Keyword or Vector | Sets how the AI searches documents | vector |
| System version | Version label for the AI system | Tracks which version was tested | v1.2.0 |
| Notes | Free text notes | Provides context for this experiment | Testing with updated March documents |

---

### 6. What Happens After the Batch Experiment

After clicking "Run Batch Experiment":
- A new evaluation run is created with the given name and settings.
- The system processes every question in the dataset one by one.
- For each question: retrieves chunks, generates an answer, saves both.
- If auto-evaluate was enabled: the AI judge scores each answer.
- A background job record tracks the progress.
- After completion, the run appears in the Experiment Leaderboard.
- The run's status changes to "completed."
- Retrieval metrics (hit rate, precision, recall, MRR) are calculated.

---

### 7. Simple Summary

Batch Experiments run the full AI evaluation automatically for all questions at once. Fill in the run name, select the dataset and documents, choose retrieval mode, and click "Run Batch Experiment." The system does everything — RAG for every question, optional auto-scoring, and summary metrics. Results appear in the Leaderboard when done.

---

---

# FEATURE 15: RUN COMPARISON

--------------------------------------------------
## Feature Name: Comparing Multiple Evaluation Runs
--------------------------------------------------

### 1. Purpose of This Feature

After running multiple experiments with different settings (e.g., keyword vs. vector retrieval, different model versions), the Run Comparison feature lets you see them side by side to determine which configuration performs best.

- **What it does:** Displays a detailed side-by-side comparison of two or more evaluation runs, showing metric differences and which run performed better on each question.
- **Why you need it:** Making a decision about which AI configuration to deploy requires knowing how each one compares.
- **When to use it:** After completing two or more batch experiments, when you want to select the best configuration.
- **What problem it solves:** Removes guesswork from AI improvement decisions by showing data-driven comparisons.

---

### 2. Before You Start

- At least two completed evaluation runs in the same project.
- Admin, Evaluator, or Viewer role (read access is sufficient).

---

### 3. Where to Find This Feature

1. Open your project's **Project Setup Page**.
2. Scroll to the **"Run Comparison"** panel.
3. Expand the section.

---

### 4. Step-by-Step Use

**Step 1: Open the Run Comparison panel**  
Expand the Run Comparison panel on the Project Setup Page.

**Step 2: Select runs to compare**  
A list of all runs in this project appears as checkboxes. Check the boxes next to the runs you want to compare.
- You must select at least 2 runs.
- You can select more than 2.
- Example: Select "Run A — Keyword Search" and "Run B — Vector Search."

**Step 3: Click "Compare selected runs"**  
Click the **"Compare selected runs"** button.

**Step 4: Read the comparison results**  
The comparison shows several sections:

**Run Metadata:** A table showing each run's name, retrieval mode, model, and system version — so you know exactly what configuration each run used.

**Metric Deltas vs. Baseline:** Shows how much each run's metrics improved or decreased compared to the first (baseline) run. Positive numbers mean improvement. Negative numbers mean the run performed worse.
- Metrics compared include: average overall score, hit rate, human review completion, judge agreement, error count.

**Question-Level Comparison:** For every question in the dataset, shows which run produced the best answer and what scores each run got. You can see at a glance:
- Which questions improved across runs.
- Which questions got worse.
- Which run got the best score for each question.

**Step 5: Identify the best configuration**  
Look at the deltas and question-level results to decide which configuration is best. The run with the highest overall score and fewest errors is generally the strongest candidate for production.

---

### 5. Output After Comparison

**Output Name:** Run Comparison Report  
**What the user will see:** Side-by-side tables showing metric deltas, per-run scores, and question-by-question best-run indicators.  
**What it means:** Which configuration of your AI system performs best.  
**Why it is useful:** Guides the decision about which version to deploy or submit for production readiness review.

---

### 6. Simple Summary

Run Comparison lets you select two or more completed experiments and see them side by side. Metric deltas show improvement over the baseline. Question-level results show which run was best for each individual question. Use this to pick the strongest AI configuration.

---

---

# FEATURE 16: EXPERIMENT LEADERBOARD

--------------------------------------------------
## Feature Name: Experiment Leaderboard
--------------------------------------------------

### 1. Purpose of This Feature

The Experiment Leaderboard ranks all evaluation runs in the project from best to worst using a single composite score. It gives you an at-a-glance view of how each experiment performed.

- **What it does:** Ranks all runs in the project using a combined score that factors in CLEAR-RAG scores, review completion, retrieval hit rate, judge calibration, and error counts.
- **Why you need it:** When you have 5, 10, or 20 different experiments, the leaderboard quickly shows you which performed best.
- **When to use it:** After completing multiple experiments, to select the best configuration.
- **What problem it solves:** Eliminates the need to manually compare many runs. One table shows the ranking.

---

### 2. Where to Find This Feature

1. Open your project's **Project Setup Page**.
2. Scroll to the top — the **"Experiment Leaderboard"** panel is prominently displayed.

---

### 3. Understanding the Leaderboard

The leaderboard table shows one row per run:

| Column | What It Means |
|---|---|
| Rank | Position (1 = best) |
| Run Name | The name you gave this experiment |
| Average Score | Average CLEAR-RAG score across all evaluated answers |
| Review % | Percentage of answers that have been reviewed and approved by a human |
| Hit Rate | Percentage of questions where the correct document was retrieved |
| Judge Agreement | How closely the automated judge agreed with human scores |
| Error Count | Total number of errors tagged in this run |
| Quality Gate | Overall production readiness status (pass/warn/fail) |
| Open Run | Link to view the full run details |

**Leaderboard Score:** A composite number calculated from all the above factors. Higher is better.

**Quality Gate values:**
- `release_candidate` — This run has passed all quality checks and is ready for production review.
- `needs_review` — Evaluation is mostly complete but requires more human review.
- `needs_error_review` — Has high or critical errors that must be fixed before production.
- `scored` — Scored but not fully reviewed yet.
- `no_outputs` — No outputs generated yet.
- `blocked_critical_errors` — Critical errors block this run from production.

---

### 4. Simple Summary

The Leaderboard ranks all your experiments from best to worst. The top-ranked run is your best-performing AI configuration. Check the Quality Gate column to see which runs are ready for production review. Click "Open run" on any row to see full details of that experiment.

---

---

# FEATURE 17: PRODUCTION READINESS

--------------------------------------------------
## Feature Name: Production Readiness Quality Gates
--------------------------------------------------

### 1. Purpose of This Feature

Before declaring an AI system "ready for real use," it must pass a series of quality checks called "gates." The Production Readiness panel runs these checks automatically and shows you exactly which gates pass, warn, or fail.

- **What it does:** Checks 8 quality criteria and shows pass/warn/fail status for each one.
- **Why you need it:** Prevents low-quality AI systems from being deployed to real users.
- **When to use it:** After completing evaluations and human review, when deciding whether the system is ready to go live.
- **What problem it solves:** Replaces subjective "it seems good enough" decisions with objective, measurable quality standards.

---

### 2. Before You Start

- A completed evaluation run with scores and human review.
- Admin, Evaluator, or Viewer role.

---

### 3. Where to Find This Feature

1. Open an evaluation run page.
2. Scroll to the **"Production Readiness"** section.
3. Expand it to see all gate results.

---

### 4. Understanding the Eight Production Gates

**Gate 1: run_completed**  
- What it checks: Has the RAG pipeline finished running for all questions?
- Pass condition: All questions have been processed.
- What to do if it fails: Go back to Batch Experiment or run RAG for individual questions until all are covered.

**Gate 2: answer_coverage**  
- What it checks: Has every question received at least one generated answer?
- Pass condition: All test questions have answers.
- What to do if it fails: Check which questions have no answers and run the AI for those questions.

**Gate 3: human_review_complete**  
- What it checks: Have all scored answers been reviewed and approved by a human?
- Pass condition: 100% of evaluations are approved.
- What to do if it fails: Go to the Evaluation Review panel and approve pending items.

**Gate 4: minimum_score**  
- What it checks: Is the average CLEAR-RAG overall score at least 4.0 out of 5.0?
- Pass condition: Average score ≥ 4.00.
- What to do if it fails: Identify weakly-scoring questions. Improve the AI's retrieval, prompting, or document quality.

**Gate 5: retrieval_hit_rate**  
- What it checks: Did the system retrieve the correct document for at least 80% of questions?
- Pass condition: Hit rate ≥ 0.80 (80%).
- What to do if it fails: Improve document indexing, add more relevant documents, or tune retrieval settings.

**Gate 6: missing_evidence**  
- What it checks: Are there any questions for which no relevant document was found at all?
- Pass condition: Missing evidence count = 0.
- What to do if it fails: Add or improve documents for the questions with no evidence.

**Gate 7: judge_calibration**  
- What it checks: Does the automated judge's scores agree with human scores at least 80% of the time (within one point)?
- Pass condition: Within-one agreement ≥ 80% (or fewer than the minimum paired answers needed to check).
- What to do if it fails: Review cases where judge and human disagree significantly. Consider re-running automated evaluation.

**Gate 8: blocking_errors**  
- What it checks: Are there any high or critical severity error tags on any answer?
- Pass condition: Zero high/critical errors.
- What to do if it fails: Fix the issues that caused those errors and re-run the evaluation, or reclassify the errors if they were mislabeled.

---

### 5. Overall Production Status

At the top of the Production Readiness panel:
- **"Ready for Production: YES"** (shown in green) — All 8 gates pass. This run meets production standards.
- **"Ready for Production: NO"** (shown in red) — One or more gates failed. The system is not ready.

---

### 6. Output After Checking

**Output Name:** Production Readiness Gate Report  
**What the user will see:** Eight gates, each showing pass (green), warning (yellow), or fail (red) status, along with the observed value and a message.  
**What it means:** Whether this AI configuration meets the minimum quality threshold for deployment.  
**Why it is useful:** Provides a defensible, documented basis for production deployment decisions.

---

### 7. Example Scenario

An evaluator checks production readiness for the "Vector Search — HR Dataset v2.0" run:

- run_completed: ✅ PASS — All 47 questions processed.
- answer_coverage: ✅ PASS — All 47 questions have answers.
- human_review_complete: ✅ PASS — 100% reviewed and approved.
- minimum_score: ⚠️ WARN — Average score is 3.85, just below the 4.0 threshold.
- retrieval_hit_rate: ✅ PASS — Hit rate is 0.87 (87%).
- missing_evidence: ✅ PASS — All questions have supporting evidence.
- judge_calibration: ✅ PASS — 83% within-one agreement.
- blocking_errors: ❌ FAIL — 2 critical hallucination errors found.

Result: **NOT ready for production.** The team must address the 2 hallucinations and improve the score for weaker questions before resubmitting.

---

### 8. Simple Summary

The Production Readiness panel runs 8 automatic quality checks. All 8 must pass (green) before the AI system is approved for real use. Check this after every experiment to understand exactly what needs improvement. A green "Ready for Production: YES" means the system is deployment-ready.

---

---

# FEATURE 18: REPORT BUILDER

--------------------------------------------------
## Feature Name: Generating Evaluation Reports
--------------------------------------------------

### 1. Purpose of This Feature

The Report Builder lets you generate a professional, structured evaluation report for any completed run. You can customize it for different audiences — executives who want a high-level summary, technical teams who need deep metrics, or auditors who need a compliance record.

- **What it does:** Generates a formatted Markdown report covering evaluation results, scores, retrieval metrics, and recommendations.
- **Why you need it:** Sharing raw data from a database is not useful for stakeholders. A formatted report explains findings clearly.
- **When to use it:** After evaluations and human review are complete, when you need to share or archive results.
- **What problem it solves:** Eliminates manual report writing. Produces a professional document in one click.

---

### 2. Before You Start

- A completed evaluation run (with scores preferred, but report can be generated at any stage).
- Admin or Evaluator role.

---

### 3. Where to Find This Feature

1. Open an evaluation run page.
2. Scroll to the **"Report Builder"** section.
3. Expand it to see the report generation form.

---

### 4. Step-by-Step Use

**Step 1: Open the Report Builder section**  
Expand the Report Builder section on the run page.

**Step 2: Enter a Report Title**  
In the **"Title"** field, type the title for the report.
- Example: `HR Chatbot Evaluation — Q1 2025 Final Report`
- Example: `Vector Search vs. Keyword Search — March 2025 Technical Review`

**Step 3: Select the Audience**  
Click the **"Audience"** dropdown and select who will read this report:
- **`executive`** — Senior management. The report focuses on high-level findings: readiness status, overall scores, and key recommendations. Technical details are minimized.
- **`technical`** — Engineers and data scientists. The report includes detailed metrics: dimension scores, retrieval precision/recall, token counts, calibration tables, per-question breakdowns.
- **`audit`** — Compliance officers and auditors. The report focuses on governance: who ran what, when, which scores were overridden, error taxonomy, and decision audit trail.

**Step 4: Select Report Sections**  
Check the boxes next to the sections you want to include:
- **Overview** — Run name, system version, model settings, question and answer counts. Always recommended.
- **Readiness** — Production readiness gate status. Recommended for executive and audit reports.
- **Scores** — CLEAR-RAG dimension averages and overall scores with visual progress bars.
- **Retrieval** — Hit rate, precision@3, recall@3, MRR, chunk coverage, missing evidence count.
- **Calibration** — Human vs. automated judge agreement metrics. For technical reports.
- **Errors** — Error taxonomy summary: counts by category and severity.
- **Questions** — Full question-by-question results table: question text, scores, retrieval metrics.

**Step 5: Click "Generate Report"**  
Click the **"Generate Report"** button. The system compiles the report from the run's data.

**Step 6: Read the generated report**  
The Markdown report appears on the page. It is formatted with headers, tables, bullet points, and progress bar representations.

**Step 7: Copy the report**  
The report text can be copied and pasted into:
- A Word document
- A Confluence/Notion page
- An email
- A PDF generator

Alternatively, you can queue the report as a Background Job using "Queue Report" if you want it processed in the background.

---

### 5. Input Data Required

| Field Name | What User Should Enter | Why This Is Needed | Example |
|---|---|---|---|
| Title | The report title | Identifies the report document | HR Chatbot Q1 2025 Final Report |
| Audience | Select executive / technical / audit | Shapes the content and depth of the report | executive |
| Sections (checkboxes) | Choose which sections to include | Customizes report content | Overview, Readiness, Scores, Errors |

---

### 6. Understanding the Report Output

**Overview Section:**  
Shows run name, when it ran, how many questions, answers, and scores were recorded. Gives context for everything else.

**Production Readiness Section:**  
Shows each gate's pass/fail status. Clearly states "Ready for Production: YES/NO."

**CLEAR-RAG Scores Section:**  
Shows average scores for each of the five dimensions as both numbers and visual bars. Also shows overall average, how many answers were reviewed, and how many were approved.

**Retrieval Evaluation Section:**  
Shows hit rate (%), precision, recall, MRR. Tells you how well the AI finds the right documents.

**Judge Calibration Section:**  
Shows how often the automated judge agreed with human reviewers. A table shows per-dimension agreement rates.

**Error Taxonomy Section:**  
Shows a breakdown of all errors by category and severity. For example: "3 hallucinations (2 critical, 1 high), 5 retrieval misses (medium)."

**Question Results Section:**  
A table with every question, its scores, and its retrieval metrics. The most detailed section — useful for technical and audit reports.

---

### 7. Simple Summary

The Report Builder generates a professional evaluation report in one click. Choose a title, audience, and sections, then click "Generate Report." The Markdown output can be copied into any document. Select "executive" audience for a concise summary, "technical" for full metrics, or "audit" for a governance-focused record.

---

---

# FEATURE 19: EXPORT (CSV AND JSON)

--------------------------------------------------
## Feature Name: Exporting Evaluation Results
--------------------------------------------------

### 1. Purpose of This Feature

Export lets you download the full evaluation results as a CSV spreadsheet or JSON data file. This is useful for further analysis in Excel, sharing with data teams, or archiving results outside the system.

- **What it does:** Creates a downloadable file containing all evaluation data from a run.
- **Why you need it:** Some users need to analyze results in Excel or import them into other tools.
- **When to use it:** After evaluation is complete, when you need a copy of the results outside the system.

---

### 2. Where to Find This Feature

1. Open an evaluation run page.
2. Scroll to the **"Evaluation Summary Analytics"** section.
3. Find the **"Export CSV"** and **"Export JSON"** buttons.

---

### 3. Step-by-Step Use

**Step 1: Open the Evaluation Summary Analytics section**  
Find and expand the analytics section on the run page.

**Step 2: Click "Export CSV" for a spreadsheet**  
Click the **"Export CSV"** button. A CSV file downloads to your computer.

**Step 3: Open the CSV in Excel or Google Sheets**  
Open the downloaded file. Each row represents one question. Columns include:

| Column | What It Contains |
|---|---|
| question_id | Unique question identifier |
| question_text | The full question |
| question_type | Type of question |
| expected_source | Expected source document |
| answer_text | The AI's generated answer |
| model_name | AI model used |
| input_tokens | Words/tokens the model read |
| output_tokens | Words/tokens in the answer |
| generation_time_ms | How long the answer took to generate |
| estimated_cost | Estimated API cost |
| citation_quality_score | Score 1-5 |
| latency_cost_score | Score 1-5 |
| evidence_faithfulness_score | Score 1-5 |
| answer_relevance_score | Score 1-5 |
| retrieval_quality_score | Score 1-5 |
| overall_score | Average of 5 scores |
| evaluation_mode | human or automated |
| review_status | approved / pending / needs_revision |
| hit_rate | Per-question retrieval hit rate |
| precision_at_k | Precision@3 |
| recall_at_k | Recall@3 |

**Step 4: Click "Export JSON" for structured data**  
Click **"Export JSON"** for a complete machine-readable export including:
- Run metadata and configuration.
- Summary statistics.
- Full question results array.
- Retrieval metrics.
- Dimension averages.
- Leaderboard metadata.

---

### 5. Simple Summary

Export CSV gives you a spreadsheet with one row per question and all scores as columns. Export JSON gives a complete structured data file with all run metadata and metrics. Both can be used for further analysis, archiving, or sharing with other teams.

---

---

# FEATURE 20: BACKGROUND JOBS

--------------------------------------------------
## Feature Name: Background Jobs Management
--------------------------------------------------

### 1. Purpose of This Feature

Some tasks take a long time to complete — running RAG for 100 questions, auto-evaluating 100 answers, generating a large report. Background Jobs run these tasks in the background so you do not have to wait on the page and can continue working.

- **What it does:** Queues long-running tasks and tracks their progress.
- **Why you need it:** You cannot wait on a page for 10 minutes while a large experiment processes.
- **When to use it:** When running large experiments, automated evaluations, or generating reports.
- **What problem it solves:** Allows long tasks to run without blocking your screen or requiring you to stay on the page.

---

### 2. Where to Find This Feature

1. Open an evaluation run page.
2. Scroll to the **"Background Jobs"** section.
3. Expand it to see queued, running, and completed jobs.

---

### 3. Step-by-Step Use

**Step 1: Open the Background Jobs panel**  
Expand the Background Jobs section. You will see a list of all jobs for this run and three queue buttons:
- **"Queue RAG Execution"** — Queues the RAG pipeline to run for all questions in this run.
- **"Queue Auto-Evaluation"** — Queues automated scoring of all answers using the AI judge.
- **"Queue Report"** — Queues report generation for this run.

**Step 2: Queue a job**  
Click the relevant button. A job record is created immediately with status "queued."

**Step 3: Monitor job progress**  
The job list shows each job's:
- **Type:** rag_execution / auto_evaluation / report_builder
- **Status:** queued → running → completed (or failed)
- **Current step:** Which processing step the job is on (e.g., "Processing question 12 of 47")

Click **"Refresh"** to update job statuses.

**Step 4: Check for completion**  
When the status shows "completed," the job results are ready. For RAG jobs, questions now have answers. For auto-evaluation jobs, answers now have scores. For report jobs, the Markdown report is available.

**Step 5: Handle failed jobs**  
If a job shows "failed," check the error message shown in the job record. Common causes:
- Gemini API key is missing or expired.
- No questions in the run.
- No documents to search.

Contact your system administrator if the error is unclear.

---

### 4. Simple Summary

Background Jobs let you run long tasks (RAG execution, auto-evaluation, report generation) without waiting on the page. Queue a job, then come back later and click Refresh to see when it is done. If a job fails, check the error message and address the underlying issue.

---

---

# FEATURE 21: AUDIT TRAIL AND GOVERNANCE

--------------------------------------------------
## Feature Name: Audit Trail and Governance Dashboard
--------------------------------------------------

### 1. Purpose of This Feature

The Audit Trail records every action every user takes in the system — who created what, who changed what score, who approved what review, and when. The Governance Dashboard summarizes this activity.

- **What it does:** Maintains a permanent, tamper-evident log of all user actions.
- **Why you need it:** For compliance, quality control, and accountability — especially important in regulated industries.
- **When to use it:** When you need to know who did what and when, for compliance audits or dispute resolution.
- **What problem it solves:** Creates a transparent record of all decisions and changes in the evaluation process.

---

### 2. Where to Find This Feature

**Project-level Audit Trail:**
1. Open the project's **Project Setup Page**.
2. Scroll to the **"Audit Trail & Governance"** panel.
3. Expand it.

**Run-level Audit Trail:**
- Navigate to any evaluation run page.
- Find the "Audit Trail" section on that run page.
- The API also provides `/projects/{id}/governance-summary` for a full governance report (needs confirmation of frontend visibility).

---

### 3. Understanding the Audit Trail Panel

The Audit Trail panel shows:

**Summary Statistics:**
- **Total Events:** How many actions have been recorded in this project.
- **Active Actors:** How many different users have performed actions.
- **Event Type Counts:** Breakdown of action types (create, update, delete, review, etc.).
- **Entity Type Counts:** Breakdown by what was acted on (project, document, question, evaluation, etc.).

**Recent Activity List:**
A chronological list of recent events showing:
- Who performed the action (user name)
- What they did (created, updated, approved, etc.)
- What they did it to (which document, question, or evaluation)
- When it happened (timestamp)

---

### 4. Simple Summary

The Audit Trail automatically records every action in the system. You do not need to do anything to enable it — it works automatically. Use it to see who changed what and when. The Governance Dashboard at the project level shows a summary of all activity, actors, and event types. This is essential for compliance reporting and accountability.

---

---

# FEATURE 22: JUDGE CALIBRATION

--------------------------------------------------
## Feature Name: Human vs. Automated Judge Calibration
--------------------------------------------------

### 1. Purpose of This Feature

Judge Calibration measures how well the automated AI judge's scores match human reviewer scores. When both a human and the automated judge have scored the same answer, you can compare them.

- **What it does:** Shows agreement statistics between human scores and automated judge scores for every CLEAR dimension.
- **Why you need it:** If the judge frequently disagrees with humans, its automated scores cannot be trusted for production decisions.
- **When to use it:** After both human evaluations and automated evaluations have been run on the same set of questions.

---

### 2. Where to Find This Feature

1. Open an evaluation run page.
2. Scroll to the **"Judge Calibration"** section.
3. Expand it.

---

### 3. Understanding the Judge Calibration Panel

**Overall Metrics:**
- **Paired Answer Count:** How many answers have both human and automated scores (needed for comparison).
- **Exact Agreement %:** Percentage of answers where human and judge gave the exact same score.
- **Within-One Agreement %:** Percentage where human and judge scores differed by 1 point or less.
- **Average Overall Delta:** Mean difference between human and judge scores. Positive means judge scores higher; negative means judge scores lower.
- **Bias Direction:** "aligned" = scores match well; "automated_under_scores" = judge is more harsh; "automated_over_scores" = judge is more lenient.

**Per-Dimension Metrics (in a table):**
For each of the five CLEAR dimensions:
- Paired score count
- Average delta (judge minus human)
- Exact agreement %
- Within-one agreement %
- Who scored higher more often

**Answer-Level Comparison Table:**
Each row shows one answer with both the human score and the judge score side by side, for all five dimensions.

---

### 4. Interpreting Calibration Results

**Good calibration:** Within-one agreement ≥ 80%. The judge's scores are reliable enough to use as primary scores.

**Poor calibration:** Within-one agreement < 80%. The judge frequently disagrees with humans. Review cases where disagreement is largest. The automated judge may need adjustment.

**Bias direction matters:**
- If "automated_over_scores": the judge thinks answers are better than humans do. This is a risk — poor answers may slip through.
- If "automated_under_scores": the judge is stricter than humans. This is less dangerous but may reject acceptable answers.

---

### 5. Simple Summary

Judge Calibration compares automated scores to human scores. It shows how often they agree and in which direction the judge leans. Good calibration (80%+ within-one agreement) means automated scoring is reliable. Poor calibration means more human review is needed. This panel appears only when both human and automated scores exist for the same answers.

---

---

# FEATURE 23: EDIT AND UPDATE

--------------------------------------------------
## Feature Name: Editing Existing Records
--------------------------------------------------

### 1. Purpose of This Feature

After saving a project, document, question, or evaluation run, you may need to correct a mistake or update information. The Edit features let you update most records without deleting and recreating them.

---

### 2. What Can Be Edited

| Record Type | What Can Be Changed | How to Access Edit |
|---|---|---|
| Project | Name, system type, target users, description | Navigate to project, find edit action (PATCH endpoint) |
| Source Document | Title, document type, version | Find document in list, use edit action |
| Test Question | Question text, question type, expected source | Find question in list, use edit action |
| Evaluation Run | Name, system version, notes | Find run, use edit action |
| CLEAR-RAG Scores | All five scores, reviewer notes, suggested improvement | Find evaluation record, use update or review action |
| Error Tags | Category, severity, notes, evidence reference | Find error tag, use edit action |

---

### 3. General Edit Process

1. Navigate to the record you want to edit.
2. Find the edit option (usually a pencil icon, "Edit" button, or direct field editing).
3. Update the information.
4. Save the changes.
5. The updated information appears immediately.
6. All edits are recorded in the Audit Trail.

---

### 4. Important Notes

- Score overrides must go through the **Evaluation Review** process (not the original scoring form) to ensure proper documentation.
- Editing questions that have already been used in completed runs will not change the past run's results — only future runs.
- All edits are logged in the Audit Trail with the editor's name and timestamp.

---

### 5. Simple Summary

Most records in CLEAR-RAG can be edited after creation. Navigate to the record, use the edit action, update the fields, and save. All edits are logged automatically in the Audit Trail. Score changes should go through the Evaluation Review process to maintain proper documentation.

---

---

# FEATURE 24: DELETE

--------------------------------------------------
## Feature Name: Deleting Records
--------------------------------------------------

### 1. Purpose of This Feature

When a record is no longer needed — a wrong document was uploaded, a test question is outdated, a run had a major error — delete removes it from the system.

---

### 2. What Can Be Deleted

| Record Type | Effect of Deletion | How to Access |
|---|---|---|
| Project | Removes entire project and all related data (documents, questions, runs, scores, errors) | Admin role required |
| Source Document | Removes document and its chunks/embeddings | Find document in list, use delete action |
| Test Question | Removes question from the project | Find question in list, use delete action |
| Evaluation Run | Removes run and all its outputs (chunks, answers, scores, errors) | Find run, use delete action |
| Retrieved Chunk | Removes single retrieved chunk from a question result | Find chunk in run, use delete action |
| Generated Answer | Removes single answer from a question result | Find answer in run, use delete action |
| CLEAR-RAG Evaluation | Removes score record for one answer | Find evaluation, use delete action |
| Error Tag | Removes specific error annotation | Find error tag, use delete action |

---

### 3. Important Warnings

**Deletion is permanent.** Most deletions cannot be undone. Be very careful before deleting.

**Cascade deletion:** Deleting a parent record deletes all its child records. For example:
- Deleting a **project** deletes ALL documents, questions, runs, scores, and error tags inside it.
- Deleting an **evaluation run** deletes ALL chunks, answers, scores, and error tags for that run.

**Before deleting, always ask:**
- Is this data needed for any report or comparison?
- Have results been exported or archived?
- Could this data be needed for audit purposes?

---

### 4. Simple Summary

Deletion permanently removes records. Parent deletions cascade — deleting a project removes everything inside it. Always export data before deleting a run or project. Only Admins can delete projects. Deletions are logged in the Audit Trail.

---

---

# FEATURE 25: ERROR MESSAGES

--------------------------------------------------
## Feature Name: Understanding Error Messages
--------------------------------------------------

### 1. Purpose of This Feature

When something goes wrong, the system shows an error message. This section explains the most common errors and what to do.

---

### 2. Common Error Messages

**"Invalid credentials"**  
Cause: Wrong email or password at login.  
Fix: Check your email spelling. If you forgot your password, contact your system administrator.

**"Email already registered"**  
Cause: You are trying to create an account with an email already in the system.  
Fix: Try logging in instead of registering.

**"Project name is required"**  
Cause: You left the Project Name field blank.  
Fix: Enter a name before clicking Create project.

**"File type not supported"**  
Cause: You tried to upload a file format the system does not accept.  
Fix: Use only .pdf, .docx, .txt, .csv, or .md files.

**"Document must be indexed before vector search"**  
Cause: You selected Vector retrieval mode but the document has not been indexed yet.  
Fix: Go to Source Documents and click "Index" for each document first.

**"No questions found in dataset"**  
Cause: The CSV/JSON file you imported was empty or incorrectly formatted.  
Fix: Check that the file has the correct column headers: question_text, question_type, expected_source.

**"Gemini API error"**  
Cause: The AI system (Gemini) could not be reached, or the API key is invalid.  
Fix: Contact your system administrator to check the Gemini API key configuration.

**"Background job failed"**  
Cause: An error occurred during a long-running task.  
Fix: Check the error message in the Background Jobs panel. Common causes: no documents, no questions, API failure. Address the root cause and queue the job again.

**"You do not have permission to perform this action"**  
Cause: Your user role (Viewer) does not have permission for this action.  
Fix: Ask an Admin to upgrade your role to Evaluator if you need to create or edit records.

**"Score must be between 1 and 5"**  
Cause: You entered a score outside the valid range.  
Fix: Enter a whole number between 1 and 5.

---

### 3. Simple Summary

Error messages tell you exactly what went wrong and why. Read the message carefully, find the relevant fix in this section, and try again. If an error is unclear, contact your system administrator and describe the exact message you saw.

---

---

# FEATURE 26: COMMON USER MISTAKES

--------------------------------------------------
## Feature Name: Common Mistakes and How to Avoid Them
--------------------------------------------------

### 1. Starting Evaluations Without Documents Indexed for Vector Search

**What happens:** You run a batch experiment with Vector mode, but no documents were indexed. The AI retrieves nothing and scores are 0.  
**How to avoid:** Always index documents before using Vector mode. Keyword mode works without indexing.

### 2. Using the Same Run for Multiple Different Experiments

**What happens:** You change the settings mid-run, mixing results from different configurations. The leaderboard score is meaningless.  
**How to avoid:** Create a new run for every experiment. Keep one configuration per run.

### 3. Forgetting to Set Expected Source on Questions

**What happens:** The system cannot calculate retrieval hit rate, precision, or recall. All retrieval metrics show 0%.  
**How to avoid:** Always enter the document name in "Expected source" for every question.

### 4. Approving All Automated Scores Without Reading Them

**What happens:** Low-quality automated scores pass review and the run incorrectly shows "Ready for Production."  
**How to avoid:** Read the judge reasoning for each score before approving. Override scores that seem wrong.

### 5. Deleting a Run With Important Results Without Exporting First

**What happens:** You lose all evaluation data permanently.  
**How to avoid:** Always export CSV and JSON before deleting any completed run.

### 6. Importing the Same Question Dataset Twice

**What happens:** Duplicate questions inflate the question count and create double results per question.  
**How to avoid:** Check the Question Datasets list before importing. If the dataset already exists, skip the import.

### 7. Not Waiting for Background Jobs to Complete

**What happens:** You check results before the job finishes and see incomplete or missing data.  
**How to avoid:** Click "Refresh" and wait until the job status shows "completed" before reviewing results.

### 8. Scoring Answers Without Reading the Retrieved Chunks

**What happens:** Evidence Faithfulness and Retrieval Quality scores are inaccurate.  
**How to avoid:** Always read the retrieved chunks before scoring. The AI's answer quality depends entirely on what was retrieved.

### 9. Running Vector Search on Documents Without Embeddings

**What happens:** The vector search finds no matches or returns irrelevant results.  
**How to avoid:** Click "Index" on every document before using Vector mode.

### 10. Creating Projects With Generic Names

**What happens:** When you have 10 projects, "Project 5" tells you nothing.  
**How to avoid:** Always name projects with the system name, test type, and date: "Customer Support Bot — Vector Search Test — March 2025."

---

---

# FEATURE 27: FULL START-TO-FINISH WORKFLOW EXAMPLE

--------------------------------------------------
## Complete Workflow: Evaluating an HR Knowledge Assistant from Start to Finish
--------------------------------------------------

This section walks through the entire process of setting up, running, and completing an evaluation from scratch.

---

### Scenario

A company has built an internal HR chatbot that answers employee questions about leave policies, benefits, and remote work. The HR team wants to evaluate whether this chatbot is accurate, reliable, and ready for company-wide deployment.

**Team:**
- **Sarah (Admin):** Set up the system and manages user accounts.
- **James (Evaluator):** Runs experiments and scores answers.
- **Linda (Viewer):** Reviews final reports.

---

### Step 1: Sarah Creates User Accounts

1. Sarah registers first at the CLEAR-RAG website. She becomes **Admin**.
2. James registers. He becomes **Viewer** by default.
3. Sarah logs in, finds a user management section, and upgrades James to **Evaluator**.
4. Linda registers and remains a **Viewer** (appropriate since she only reviews reports).

---

### Step 2: James Creates a New Project

1. James logs in and clicks "New project."
2. He fills in:
   - Project name: `HR Chatbot Evaluation — Q1 2025`
   - System type: `internal_knowledge_assistant`
   - Target users: `All company employees`
   - Description: `Evaluating accuracy and retrieval quality of the HR chatbot for policy-related questions.`
3. He clicks "Create project." The project workspace opens.

---

### Step 3: James Uploads Source Documents

The HR chatbot uses three documents. James uploads all three.

1. In the Source Documents section, James clicks "Add document."
2. He uploads: Title = `HR Leave Policy 2024`, Type = `policy`, File = `leave_policy_2024.pdf`.
3. He repeats for: `Employee Benefits Guide 2024` (type: guide) and `Remote Work Policy 2024` (type: policy).
4. All three documents appear in the list.
5. James clicks "Index" on each document to prepare them for vector search.

---

### Step 4: James Imports a Question Dataset

James has prepared 30 test questions in a CSV file:

```csv
question_text,question_type,expected_source
How many annual leave days do employees get?,simple_factual,HR Leave Policy 2024
What is the sick leave entitlement for part-time staff?,conditional,HR Leave Policy 2024
Can I work from home full-time?,conditional,Remote Work Policy 2024
...
```

1. James goes to the Question Datasets section.
2. He enters: Dataset name = `HR Q1 2025 Test Set`, Version = `v1.0`.
3. He selects the CSV file and clicks "Import."
4. All 30 questions are imported. The dataset appears with question count = 30.

---

### Step 5: James Runs Batch Experiment A (Vector Search)

1. James opens the Batch Experiment section.
2. He fills in:
   - Run name: `Vector Search — Gemini Flash — HR Dataset v1.0`
   - Dataset: `HR Q1 2025 Test Set`
   - Documents: All three HR documents selected.
   - Retrieval mode: Vector
   - System version: `v1.0.0`
   - Auto-evaluate: ON
3. He clicks "Run Batch Experiment."
4. He monitors the Background Jobs panel. After 8 minutes, the job shows "completed."
5. The run appears in the Leaderboard with initial scores.

---

### Step 6: James Reviews Automated Scores

1. James opens the run page for "Vector Search — Gemini Flash — HR Dataset v1.0."
2. He opens the Evaluation Review panel.
3. He works through all 30 items:
   - For most, the automated scores look reasonable. He approves them.
   - For Question 14 ("Can I work from home full-time?"), the judge gave Evidence Faithfulness = 4, but James notices the AI actually stated an incorrect policy date (hallucination). He selects "needs_revision," overrides Evidence Faithfulness to 2, adds review notes: "AI stated policy effective date as 2022. Policy document says 2023. Hallucination."
4. James adds an Error Tag for that question: Category = `hallucination`, Severity = `high`, Notes = "AI fabricated policy year as 2022."
5. After reviewing all 30, James checks the Production Readiness panel.

---

### Step 7: Checking Production Readiness

James opens the Production Readiness panel:

- run_completed: ✅ PASS
- answer_coverage: ✅ PASS
- human_review_complete: ✅ PASS (100% approved)
- minimum_score: ⚠️ WARN — Average = 3.92, slightly below 4.0 threshold.
- retrieval_hit_rate: ✅ PASS — Hit rate = 0.85
- missing_evidence: ✅ PASS
- judge_calibration: ✅ PASS — 84% within-one agreement
- blocking_errors: ❌ FAIL — 1 high severity hallucination error found.

**Result:** NOT ready for production. Two issues to fix.

---

### Step 8: James Runs Batch Experiment B (Keyword Search for Comparison)

To understand if keyword search performs differently, James creates a second run:
- Run name: `Keyword Search — Gemini Flash — HR Dataset v1.0`
- Same dataset, same documents, but Retrieval mode = Keyword.
- He runs the experiment and reviews it the same way.

---

### Step 9: James Compares Runs

1. On the Project Setup Page, James opens Run Comparison.
2. He selects both runs and clicks "Compare selected runs."
3. He sees: Vector Search scores 3.92 average, Keyword Search scores 3.74 average. Vector has higher hit rate (0.85 vs. 0.71).
4. The Leaderboard also confirms: Vector Search is ranked #1.

---

### Step 10: James Generates Reports

1. James opens the Vector Search run's Report Builder.
2. He generates three reports:
   - **Executive report:** Title = `HR Chatbot Q1 2025 Executive Summary`, Audience = executive, Sections: Overview, Readiness, Scores.
   - **Technical report:** Audience = technical, All sections checked.
   - **Audit report:** Audience = audit, Sections: Overview, Readiness, Errors.
3. He copies each report and shares with the appropriate team members.

---

### Step 11: Sarah Reviews and Exports

1. Sarah opens the project as Admin.
2. She reviews the Audit Trail — all 30 review actions by James are logged.
3. She exports the Vector Search run as CSV for the data team.
4. She notifies the team that the HR chatbot needs the hallucination issue fixed before deployment.
5. After the chatbot team fixes the issue, a new batch experiment (v1.1.0) is run. It passes all production gates and is approved for deployment.

---

### End-to-End Checklist

| Step | Action | Status |
|---|---|---|
| 1 | Register and set up user accounts | ✅ |
| 2 | Create project | ✅ |
| 3 | Upload and index source documents | ✅ |
| 4 | Import question dataset | ✅ |
| 5 | Run batch experiment | ✅ |
| 6 | Review and approve/override automated scores | ✅ |
| 7 | Add error tags for any problems found | ✅ |
| 8 | Check production readiness | ✅ |
| 9 | Compare multiple run configurations | ✅ |
| 10 | Generate and share reports | ✅ |
| 11 | Export results for archiving | ✅ |

---

---

# APPENDIX: QUICK REFERENCE

## User Roles Summary

| Role | Can Create/Edit | Can Score/Review | Can Approve Roles | Can View |
|---|---|---|---|---|
| Admin | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Evaluator | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| Viewer | ❌ No | ❌ No | ❌ No | ✅ Yes |

## CLEAR-RAG Scoring Scale

| Score | Meaning |
|---|---|
| 5 | Excellent — No issues at all |
| 4 | Good — Minor issues only |
| 3 | Acceptable — Noticeable issues but still useful |
| 2 | Poor — Significant problems |
| 1 | Very Poor — Fails completely |

## Production Gates Quick Reference

| Gate | Required Threshold | What It Checks |
|---|---|---|
| run_completed | All questions processed | RAG pipeline ran for all questions |
| answer_coverage | All questions answered | Every question has at least one answer |
| human_review_complete | 100% reviewed | All scores reviewed and approved |
| minimum_score | ≥ 4.00 average | Overall quality is at least 4/5 |
| retrieval_hit_rate | ≥ 80% | Correct document retrieved 80%+ of the time |
| missing_evidence | 0 questions | No question without supporting evidence |
| judge_calibration | ≥ 80% within-one | Automated and human scores agree 80%+ |
| blocking_errors | 0 high/critical | No serious errors found |

## Supported File Types

| Feature | Accepted Formats |
|---|---|
| Document Upload | .pdf, .docx, .txt, .csv, .md |
| Question Dataset Import | .csv, .json |
| Export | .csv (download), .json (download) |

## Error Category Quick Reference

| Category | Meaning |
|---|---|
| retrieval_miss | System failed to find relevant document |
| citation_error | AI cited wrong or non-existent source |
| hallucination | AI stated facts not in any document |
| incomplete_answer | Answer is missing important information |
| irrelevant_answer | Answer does not address the question |
| contradiction | Answer contradicts the source document |
| latency_cost | Answer was too slow or too expensive |
| format_error | Answer is in the wrong format |
| policy_ambiguity | Source document itself is unclear |
| other | Any other error type |

---

*This user guide was created for the CLEAR-RAG Evaluation System. For technical support, contact your system administrator. For feedback or corrections to this guide, report to the project team.*

*Guide Version 1.0 — May 2025*
