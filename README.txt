YOUTUBE SHORTS AUTOMATION — ANDROID SETUP
=========================================

WHAT THIS FIRST VERSION DOES
- Creates one original, text-based English Short per day.
- Uses a free neural text-to-speech voice.
- Renders a vertical 1080x1920 MP4 with FFmpeg.
- Uploads it to your YouTube channel using the official YouTube Data API.
- Runs from GitHub Actions; your Android phone is only needed for setup.

IMPORTANT LIMITS
- This is an automated template-based content system, not a free Claude/ChatGPT video-generation API.
- It uses a small built-in library of scripts. Edit VIDEOS in main.py to add your own topics.
- It creates text-card videos, not cinematic AI animation or real gameplay footage.
- Edge TTS is an unofficial community package/service and can stop working or change.
- GitHub Actions scheduled runs can be delayed. Free quotas and policies can change.
- Do not upload repetitive, low-value or misleading videos. Review YouTube monetization and reused/repetitious content policies.
- Test with YT_PRIVACY=unlisted first. Change to public only after you confirm the result.

STEP 1 — CREATE A GITHUB REPOSITORY (ON ANDROID)
1. Open https://github.com in Chrome and create/sign in to an account.
2. Tap +, choose New repository.
3. Name it yt-shorts-automation.
4. Choose Public (GitHub Actions minutes are free for public repositories).
5. Create repository.
6. Upload the files from this ZIP, keeping the exact folders:
   main.py
   requirements.txt
   .github/workflows/daily.yml
   Use Add file > Upload files in GitHub's browser interface. If hidden folders are hard to upload on mobile, create .github, then workflows, then daily.yml using Add file > Create new file; enter .github/workflows/daily.yml as its path.

STEP 2 — CREATE YOUTUBE API CREDENTIALS
1. Open https://console.cloud.google.com/ and create a project.
2. Open APIs & Services > Library. Search "YouTube Data API v3" and enable it.
3. Open Google Auth Platform / OAuth consent screen. Configure the app. If asked for audience, choose External for a personal Gmail account and add your Google account as a test user.
4. Open APIs & Services > Credentials > Create credentials > OAuth client ID.
5. If using OAuth Playground below, create a Web application OAuth client and add this exact authorized redirect URI:
   https://developers.google.com/oauthplayground
6. Save the Client ID and Client Secret privately. Never put them in source code or a public repository.

STEP 3 — GET A REFRESH TOKEN
1. Open https://developers.google.com/oauthplayground
2. Tap the settings gear. Enable "Use your own OAuth credentials" and enter the OAuth Client ID and Client Secret.
3. In Step 1, enter this scope:
   https://www.googleapis.com/auth/youtube.upload
4. Authorize APIs using the Google account that owns the YouTube channel.
5. In Step 2, exchange the authorization code for tokens.
6. Copy the Refresh token. Keep it secret.
NOTE: If your OAuth consent app remains in Testing mode, Google refresh tokens for external test apps can expire after 7 days. For long-running automation, review the app publishing/verification requirements in Google Auth Platform. Do not assume the token will last forever.

STEP 4 — ADD GITHUB SECRETS
In your repository:
Settings > Secrets and variables > Actions > New repository secret.
Create these three secrets exactly:
YT_CLIENT_ID       = OAuth Client ID
YT_CLIENT_SECRET   = OAuth Client Secret
YT_REFRESH_TOKEN   = Refresh token

STEP 5 — TEST SAFELY
1. In .github/workflows/daily.yml, temporarily change YT_PRIVACY: public to YT_PRIVACY: unlisted.
2. Open Actions > Create and upload a Short > Run workflow.
3. Wait for it to finish. Check the uploaded unlisted video in YouTube Studio.
4. If it works, change YT_PRIVACY back to public.
5. The schedule is 06:17 UTC, which is 11:02 AM Nepal time. Scheduled GitHub jobs may run late.

STEP 6 — CHANGE YOUR CONTENT
Open main.py and find:
VIDEOS = [
Add more dictionaries in the same format. Keep scripts factual, original, and safe. A video title must be under 100 characters. Keep each script concise enough for a Short.

TROUBLESHOOTING
- invalid_grant: refresh token expired/revoked; repeat Step 3 and update GitHub secret.
- quotaExceeded: check Google Cloud Console > APIs & Services > YouTube Data API quota.
- workflow does not run: ensure daily.yml is on the repository's default branch and Actions are enabled.
- ffmpeg error: check that FFmpeg installation step succeeded.
- voice generation fails: edge-tts may be temporarily unavailable; rerun later.

SECURITY
- Never share your OAuth client secret or refresh token with anyone, including in chat.
- Do not commit credentials JSON, refresh tokens, or .env files.
