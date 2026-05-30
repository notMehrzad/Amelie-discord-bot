[![English](https://img.shields.io/badge/English-🇺🇸-blue)](CONTRIBUTING.md)
[![فارسی](https://img.shields.io/badge/فارسی-🇮🇷-green)](CONTRIBUTING.fa.md)

---

# Contents

- [1. How Can You Help](#1-how-can-you-help)
- [2. Before You Start](#2-before-you-start)
    - [2.1 The Process of Adding New Commands / Features](#21-the-process-of-adding-new-commands--features)
    - [2.2 What Happens When You Open An Issue?](#22-what-happens-when-you-open-an-issue)
- [3. Getting Started](#3-getting-started)
    - [3.1 Setting Up The Repository](#31-setting-up-the-repository)
    - [3.2 Setting Up your Virtual Environment](#32-setting-up-your-virtual-environment)
    - [3.3 Installing Dependencies](#33-installing-dependencies)
    - [3.4 Stay Up To Date](#34-stay-up-to-date)
- [4. Start Coding](#4-start-coding)
    - [4.1 Test Your Changes](#41-test-your-changes)
    - [4.2 Check Before Committing](#42-check-before-committing)
    - [4.3 Committing](#43-committing)
- [5. Push To Your Fork And Open A Pull Request](#5-push-to-your-fork-and-open-a-pull-request)
    - [5.1 What Happens After You Submit a PR?](#51-what-happens-after-you-submit-a-pr)
    - [5.2 If Your PR Is Rejected](#52-if-your-pr-is-rejected)
- [6. Getting Help](#6-getting-help)

---

# 1. How Can You Help

Even a small bug report can help me a lot.

Whether it's code, bug reports, feature ideas, documentation improvements, or just feedback. **Anything helps move this
project forward.**

**So any contribution, of any kind, is more than welcome.**

---

# 2. Before You Start

To avoid wasting your time (and mine):

1. **Always check [open issues](https://github.com/notMehrzad/Amelie-discord-bot/issues) first. Someone might already be
   working on the thing you have in mind.**

2. **It is recommended to [open an issue](https://github.com/notMehrzad/Amelie-discord-bot/issues/new) first and wait to
   get confirmation that your contribution is wanted. This avoids working on something that might not suit Amélie and
   could be rejected.**

   > Exception: Small fixes like typos, formatting, or minor documentation improvements **do not require** an issue
   > first. Just open a direct PR for those.

## 2.1 The Process of Adding New Commands / Features

1. **[Open an issue](https://github.com/notMehrzad/Amelie-discord-bot/issues/new) with label `enhancement`.**

2. **Describe it perfectly.** explain:
    - What the main idea of the command/feature is
    - What the command/feature should do
    - What the expected output should be
    - Why it would be useful
    - Example usage

3. **Wait for review. I will check if it suits Amélie and will be useful to many.
   And only then, you (or someone else) can work on it eventually!**

## 2.2 What Happens When You Open An Issue?

When you submit and open an issue, I try to review within a few days.

**If the issue subject is fine, suitable for Amélie and can be useful, the issue stays open and you (or someone else)
can work on it.**

**If the issue subject is rejected by any reason, I will close the issue.**

---

# 3. Getting Started

**It is best to follow this workflow by following the guides below for the highest possible coding quality.**

**The following requirements must be installed first:**

- `Python 3.8.1` or greater
- `pip`
- `git`

## 3.1 Setting Up The Repository

1. **Fork this repository.**

2. **Clone your fork.**

   ```bash
   git clone https://github.com/YOUR-USERNAME/Amelie-discord-bot.git
   cd Amelie-discord-bot
   ```

3. **Add original repo as upstream.**

   ```bash
   git remote add upstream https://github.com/notMehrzad/Amelie-discord-bot.git
   ```

4. **Create your feature branch.**

   ```bash
   git checkout -b feature/your-feature-name
   ```

## 3.2 Setting Up your Virtual Environment

**It is recommended to create a virtual environment to keep your codes isolated and other installed packages in your
system will be unaffected this way.**

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 3.3 Installing Dependencies

1. **Install dependencies from `requirements.txt`.**

   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `config.json` file.**

   ```json
   {
     "TOKEN": "BOT_TOKEN",
     "ADMINS": ["ADMINS_ID"]
   }
   ```

    - Replace `BOT_TOKEN` with your testing-bot token.
    - Replace `ADMINS_ID` with your Discord account ID.

## 3.4 Stay Up To Date

**Try to pull from [upstream](https://github.com/notMehrzad/Amelie-discord-bot/tree/main) (main branch on the main
repository) occasionally to receive the latest updates. Also, if you noticed that the `requirements.txt` has changed,
that means some dependencies may have been added, removed or changed. You will need to modify your installed packages
accordingly.**

---

# 4. Start Coding

**We currently use [Black Formatter](https://github.com/psf/black) as our formatter, as it will automatically detect
whether any part of your code needs to be reformatted or not.**

**Type hints and documenting while coding is extremely encouraged.**

**So start coding and make sure your code follows our coding style and format.**

## 4.1 Test Your Changes

**Run your test bot and see if everything new works just fine.**

**Your test must satisfy these conditions:**

- Your test bot starts without error

- Your changes work as expected

- Unrelated commands still work

- Your test bot doesn't crash

## 4.2 Check Before Committing

- **Your code follows our formatter and style**

- **Your code doesn't have unnecessary comments, debug prints, etc.**

- **You have tested everything**

- **You are not committing unwanted files. The `.gitignore` file is complete**

## 4.3 Committing

**After you're done, commit the changes and make sure to write a clear commit message.**

Commit message format:

- feat: → New feature or command

- fix: → Bug fix

- docs: → Documentation changes

> You can write longer description of the commit if required.

---

# 5. Push To Your Fork And Open A Pull Request

**After you have tested everything, and only then, you can push to your fork and open a PR to the original repository.**

## 5.1 What Happens After You Submit a PR?

1. **Usually, the PR will be reviewed by me within a few days.**

2. **You might be asked to make some changes if required.**

3. **After you make all necessary changes following the above guideline, your PR will be approved and merged!**

## 5.2 If Your PR Is Rejected

**Common reasons for PR rejection could be:**

- **You didn't follow the issue-first process and someone already submitted the same PR**

- **Your code doesn't pass tests**

- **Your code doesn't fit Amélie's vision**

---

# 6. Getting Help

Stuck somewhere? Have a question?

**Open a `question` issue.**

> **Before asking:** Check existing [issues](https://github.com/notMehrzad/Amelie-discord-bot/issues) and this document
> first. Your question might already be answered.
