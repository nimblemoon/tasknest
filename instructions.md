Continue working on your Final Project during the designated three-hour development session. Your progress will 
be monitored using the application screens you create or improve, the source-code changes recorded through 
Git, and the commit activity visible in your GitHub repository. 
You are required to submit ALL the evidence described below through Microsoft Teams. 
1. APPLICATION SCREENSHOTS 
Capture screenshots of ALL application screens, pages, modules, and interfaces that you create or modify during 
today's session. 
• Capture the actual running application. Screenshots of source code alone do not satisfy this requirement. 
• Include newly developed screens and existing screens that you improved or modified. 
• Make sure the screenshots are readable and show the relevant interface or functionality. 
• Save the screenshots in a folder named APPLICATION_SCREENSHOTS. 
Suggested folder structure: 
APPLICATION_SCREENSHOTS/ 
01_Login.png 
02_Dashboard.png 
03_UserManagement.png 
04_Reports.png 
05_Settings.png 
The filenames above are examples only. Include every screen you actually created or modified. 
2. RECORD YOUR BASELINE AT 3:00 PM 
Before making changes, open a terminal in your project directory. Record the latest commit so that your work 
during the session can be compared with the state of the project at the beginning. 
git status 
git log -1 --format="%H | %an | %ad | %s" --date=iso > BASELINE_COMMIT.txt 
Keep BASELINE_COMMIT.txt. Do not overwrite it. The full commit hash in this file is your starting reference. 
3. TRACK AND COMMIT YOUR WORK USING GIT 
Continue developing your Final Project. Commit and push your changes regularly throughout the session. Do not 
wait until 6:00 PM to make only one commit. 
Use the following commands whenever you have a meaningful set of changes ready: 
git add . 
git commit -m "Describe the actual work completed" 
git push 
November 16, 2026  |  3:00 PM – 6:00 PM 
FINAL PROJECT DEVELOPMENT MONITORING 
Use meaningful commit messages, for example: “Implement student profile page” or “Fix report filtering”. If your 
local branch has no upstream configured, use git push -u origin YOUR_BRANCH the first time. Use your actual 
branch name; do not assume it is main. 
4. GENERATE YOUR GIT EVIDENCE AT 6:00 PM 
After completing your work and pushing your final commit, run the commands below from the project directory. 
These commands create text and patch files for your submission. 
4.1 Today's commit history 
git log --since="2026-11-10 15:00:00" --until="2026-11-10 18:00:00" --date=iso --pretty=format:"%h | %an | 
%ad | %s" > GIT_HISTORY.txt 
4.2 Detailed commit history and file statistics 
git log --since="2026-11-10 15:00:00" --until="2026-11-10 18:00:00" --stat --date=iso > 
GIT_COMMIT_DETAILS.txt 
4.3 Changes committed since the baseline 
Copy the full commit hash from BASELINE_COMMIT.txt and replace BASELINE_COMMIT_HASH below. Do not 
type the words BASELINE_COMMIT_HASH literally. 
git diff --binary BASELINE_COMMIT_HASH..HEAD > GIT_ALL_COMMITTED_CHANGES.patch 
4.4 Remaining uncommitted changes 
git diff --binary > GIT_UNCOMMITTED_CHANGES.patch 
4.5 Current Git status 
git status --short > GIT_STATUS.txt 
4.6 Change summary 
git diff BASELINE_COMMIT_HASH..HEAD --stat > GIT_DIFF_STAT.txt 
Again, replace BASELINE_COMMIT_HASH with the actual baseline commit hash. The baseline-to-HEAD 
commands show tracked changes committed after the baseline. The uncommitted patch records tracked changes 
that have not yet been committed. 
5. GITHUB EVIDENCE 
1. Open your GitHub repository in a web browser. 
2. Navigate to the repository's commit history. 
3. Capture screenshots showing the repository name, commit messages, and commit dates/times for today's 
work. 
4. Verify that the commits you made locally have been pushed and are visible on GitHub. 
5. Save the screenshots in a folder named GITHUB_SCREENSHOTS. 
November 16, 2026  |  3:00 PM – 6:00 PM 
FINAL PROJECT DEVELOPMENT MONITORING 
GitHub may display timestamps in a timezone different from your computer's local timezone. Use the commit 
details and timestamps when reviewing the session activity. 
6. REQUIRED SUBMISSION FOLDER 
Organize your evidence using the following structure: 
LASTNAME_FINAL_PROJECT/ 
| 
|-- APPLICATION_SCREENSHOTS/ 
|   |-- 01_Login.png 
|   |-- 02_Dashboard.png 
|   |-- 03_OtherScreens.png 
| 
|-- GITHUB_SCREENSHOTS/ 
|   |-- 01_CommitHistory.png 
|   |-- 02_Repository.png 
| 
|-- BASELINE_COMMIT.txt 
|-- GIT_HISTORY.txt 
|-- GIT_COMMIT_DETAILS.txt 
|-- GIT_DIFF_STAT.txt 
|-- GIT_ALL_COMMITTED_CHANGES.patch 
|-- GIT_UNCOMMITTED_CHANGES.patch 
|-- GIT_STATUS.txt 
 
Compress the complete LASTNAME_FINAL_PROJECT folder into one ZIP file. Replace LASTNAME with your 
surname. 
LASTNAME_FINAL_PROJECT_EVIDENCE.zip 
Upload the ZIP file to the designated Microsoft Teams assignment. Include the following details in the submission 
description: 
Student Name: 
Section: 
Project Title: 
GitHub Repository URL: 
 
Development Date: November 10, 2026 
Development Time: 3:00 PM – 6:00 PM 
 
Submitted Evidence: 
1. Application Screenshots 
2. Git Source Code Changes 
3. Git Commit History 
4. GitHub Commit History Screenshots 
5. Baseline Commit Evidence 
 
8. FINAL SUBMISSION CHECKLIST 
☐  All application screenshots are included. 
☐  All Git evidence files are included. 
☐  Baseline commit evidence is included. 
☐  All development commits have been pushed to GitHub. 
7. SUBMISSION THROUGH MICROSOFT TEAMS in .txt file. 
November 16, 2026  |  3:00 PM – 6:00 PM 
FINAL PROJECT DEVELOPMENT MONITORING 
☐  GitHub commit history screenshots are included. 
☐  The ZIP file opens successfully and contains the required folders and files. 
☐  The ZIP file has been uploaded to the correct Microsoft Teams assignment. 
9. IMPORTANT REMINDERS 
• All submitted evidence must represent your actual development work during the designated period: 3:00 PM 
to 6:00 PM, November 16, 2026. 
• Commit and push your work regularly. A single final commit does not provide the same progress record as 
regular commits. 
• Do not fabricate screenshots, backdate commits, or submit work that you did not complete during the session. 
• Your application screenshots, source-code changes, commit history, and GitHub repository activity will be 
checked against one another. 
• Git diff does not automatically include untracked files. Make sure newly created project files are added to Git 
and committed, or otherwise account for them in your evidence. 
• Do not include passwords, API keys, access tokens, private credentials, or other secrets in your evidence or 
repository. 
• A Git commit timestamp is not independent proof of when the work was written. The baseline, regular 
commits and pushes, screenshots, and code differences will be considered together. 
• Make sure that your submission is complete before leaving the session. 
Your evaluation will be based on the actual work accomplished, the quality and completeness of your 
implementation, the verifiable source-code changes, and your documented development progress during the 
designated three-hour session. 
Failure to submit the required evidence will affect your evaluation because your development progress cannot be 
properly verified. 
YOUR SUBMISSION IS YOUR PROOF OF WORK. 
NOT TURNED IN = NOT SUBMITTED. 
Use your time wisely. Continue developing, improving, testing, and documenting your Final Project. 
November 16, 2026  |  3:00 PM – 6:00 PM 