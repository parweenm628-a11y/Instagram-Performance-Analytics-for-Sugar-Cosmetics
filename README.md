# SUGAR Cosmetics Instagram Performance Dashboard

An interactive Streamlit dashboard for exploring Instagram-style performance data.

## Files in this repository

- `app.py` — Streamlit dashboard application
- `requirements.txt` — Python packages needed to run the dashboard
- `README.md` — Project overview and setup instructions
- `sugar_cosmetics_instagram_data.xlsx` — Dataset used by the dashboard

## Features

- KPI cards for records, impressions, summed reach, likes, interactions, and engagement rate
- Filters for date range, post type, campaign, engagement source, audience emotion, and hashtag group
- Monthly trends and weekday analysis
- Content-type and campaign comparisons
- Top 10 records by likes and engagement rate
- Hashtag-group and audience analysis
- Data-quality checks
- Filter-aware summary insights

## Run locally

1. Install Python 3.10 or later.
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

6. If the Excel dataset is in the same folder as `app.py`, it loads automatically. You can also upload an `.xlsx` file from the sidebar.

## Deploy with Streamlit Community Cloud

1. Upload all four project files to a GitHub repository.
2. Open Streamlit Community Cloud and connect your GitHub account.
3. Select your repository and branch.
4. Set the main file path to `app.py`.
5. Click Deploy.

## Important data notes

- The dashboard calculates engagement rate as `(Likes + Comments + Shares + Saves) / Reach × 100` per record.
- Summed reach can count the same account more than once across records.
- The dataset does not include a unique post ID or caption. The app therefore labels rows as records, not verified unique posts.
- Hashtags are stored as groups/combinations, so group comparisons do not establish the independent impact of a single hashtag.
- Confirm whether each row represents a real post or another type of observation before treating the results as verified official brand performance.
