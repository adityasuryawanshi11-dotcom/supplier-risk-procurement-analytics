# Start here: run and share the project

## 1. Prepare your computer

Install Python 3.10 or later from [python.org](https://www.python.org/downloads/) if you do not already have it. On Windows, choose the option to add Python to your PATH if offered.

Extract the downloaded ZIP. Open the extracted `procurement-analytics` folder. It should contain `app.py`, `analytics.py`, `data`, and `static`.

## 2. Open a terminal in the project folder

**Windows:** Open the project folder in File Explorer. Click the address bar, type `cmd`, and press Enter. This opens Command Prompt in that folder. Type:

```bat
py --version
py app.py
```

If `py` is not recognized but Python is installed, try `python --version` and `python app.py` instead.

**macOS:** In Terminal, type `cd ` (with a space), drag the extracted project folder into the terminal, and press Enter. Then run:

```bash
python3 --version
python3 app.py
```

The terminal should display `Procurement analytics is running at http://127.0.0.1:8000`. Open that address in a browser. Keep the terminal open. To stop the app, return to the terminal and press `Ctrl+C`.

If the port is in use, close the other application using port 8000 and run the command again. If the page does not load, check that the server is still running and enter the exact address in the browser.

## 3. Try a two-minute demo

1. In **Overview**, point out 900 POs, 15 suppliers, and the overall late and defect rates. Explain that the data is simulated.
2. Open **Supplier analysis**, select **Horizon Rotary**, and show its risk score and contributing factors.
3. Change the weight for one risk factor and explain that the model rescales the weights to total 100%.
4. Open **Spend & cost** and explain that variance compares the actual purchase value against contracted prices; it is not a realized saving.
5. Open **Methodology** to show the inputs and limitations. Return to the default weights with **Reset defaults** before comparing to the baseline.

Read `docs/INTERVIEW_GUIDE.md` for the exact Horizon example and questions to practice.

## 4. Optional: enable AI briefs

The app works without AI. To generate a brief, you need your own OpenAI API key, API access and billing as applicable, and an internet connection. The default model is `gpt-6-luna`. A ChatGPT subscription alone is not the same as an API key. Do not share or commit your key.

In **PowerShell**, from the project folder:

```powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY"
py app.py
```

In **Windows Command Prompt**:

```bat
set OPENAI_API_KEY=YOUR_API_KEY
py app.py
```

In **macOS Terminal**:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
python3 app.py
```

Replace `YOUR_API_KEY` locally. In the app, select a supplier and click **Generate AI brief**. This sends the selected supplier's aggregate fictional metrics to OpenAI and may incur API charges. If a model or key error appears, check API access and billing. The deterministic score and rule-based recommendations do not require AI.

## 5. Share the project or publish your own copy

If you are viewing this guide in an existing public GitHub repository, you can share that repository's URL directly. If you downloaded the ZIP and want to create a separate repository of your own, follow the optional steps below. You need a GitHub account and Git installed on your computer; extracting the ZIP does not create a GitHub repository automatically.

1. Sign in to GitHub and create a **new empty repository** named `supplier-risk-procurement-analytics` (choose public or private). Do not add a README, license, or `.gitignore` during creation; this project already contains a README and `.gitignore`.
2. Open a terminal in the extracted project folder. Run these commands, replacing `YOUR_USERNAME` with your GitHub username:

   ```bash
   git init
   git add .
   git commit -m "Add supplier risk and procurement analytics demo"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/supplier-risk-procurement-analytics.git
   git push -u origin main
   ```

3. Follow Git's sign-in prompt. GitHub's web page should then show your project and README. Copy the repository URL to share with an interviewer. If you choose a private repository, the interviewer needs access to view it.

If Git asks for a commit identity first, configure **your own** name and email:

```bash
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR EMAIL"
```

Then repeat `git add .`, `git commit ...`, and the remaining commands. Keep API keys out of the repository and out of screenshots. Check `git status` before future commits.

## 6. Power BI

The package includes a ready-to-import `data/supplier_metrics.csv` plus the original transaction data. Follow `docs/POWER_BI_GUIDE.md` to create a report yourself in Power BI Desktop. The package does not include a finished Power BI `.pbix` file.
