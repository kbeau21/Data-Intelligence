# Company Intelligence System

Upload a list of companies via Excel and get back:
- **Intelligence reports** on each company (news, events, leadership changes, M&A activity)
- **Reasons to reach out** — specific, actionable suggestions based on what's happening at each company
- **Connection mapping** — discover how companies are linked (mergers, partnerships, shared events, networking groups)
- **Inroad suggestions** — when a connection involves one of your existing clients, get told exactly who to ask for an introduction

> **Connection insights are only shown when at least one of the two connected companies is marked as your client.** This keeps the focus on actionable warm introductions.

---

## Option 1: Deploy to the Cloud (Easiest — No Install Needed)

Click the button below to deploy this app to Render.com for free. You'll get a URL you can open from any browser.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kbeau21/Data-Intelligence)

After deploying, Render will give you a URL like `https://company-intelligence-xxxx.onrender.com`. Open it and upload your Excel file.

---

## Option 2: Run on Your Computer

### Windows
1. Download this project (green **Code** button > **Download ZIP** on GitHub)
2. Unzip the folder
3. Double-click **`start.bat`**
4. Your browser will open automatically

### Mac / Linux
1. Download this project (green **Code** button > **Download ZIP** on GitHub)
2. Unzip the folder
3. Open Terminal, navigate to the folder, and run: `./start.sh`
4. Your browser will open automatically

> **Note:** You need Python installed. The launcher will tell you if it's missing and how to install it.

---

## Your Excel File

Create an Excel file (`.xlsx`) with these columns:

| Company Name | Address | Client |
|---|---|---|
| Acme Corporation | 123 Main St, Springfield, IL | Yes |
| Beta Industries | 456 Oak Ave, Chicago, IL | No |
| Gamma Partners | 789 Pine Rd, Denver, CO | Yes |

- **Company Name** (required) — the name of each business
- **Address** (optional) — helps narrow search results to the right company
- **Client** (optional) — mark "Yes" for your existing clients. This controls whether you see connection insights and inroad suggestions for that company's relationships

Column names are flexible. "Company", "Business Name", "Organization" all work. The Client column accepts "Yes", "Y", "True", "1", or "X".

---

## What You'll See

### Dashboard
An overview of every company with a quick summary and the top reason to reach out.

### Company Reports
Click any company for the full report:
- **Overview** — what's happening at this company
- **Why This Company Matters** — relevance to your business
- **Reasons to Reach Out** — numbered, specific talking points (new leadership = congratulate them, expansion = offer to support, M&A = help with transition, etc.)
- **Recent News** — categorized articles with sources

### Connections
See how companies in your list are connected to each other:
- **Mergers & Acquisitions** — one company acquired or merged with another
- **Partnerships & Joint Ventures** — companies working together
- **Shared Events** — both companies at the same conference, trade show, or gala
- **Networking Groups** — same chamber of commerce, industry association, or advisory board
- **Client Relationships** — one company serves the other

When a connection involves your client, you'll see an **Inroad Suggestion** like:
> "Ask Acme Corp (your client) for an introduction to Beta Industries."

---

## Using Real Web Search

By default, the app runs with sample data so you can see how it works. To search the real web:

1. Get a free API key from [SerpAPI](https://serpapi.com/)
2. Create a file called `.env` in the project folder with:
   ```
   SEARCH_PROVIDER=serp
   SERP_API_KEY=your_key_here
   ```
3. Restart the app
