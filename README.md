# GINDUMAC_intern
A python3 GUI created with PyQt5 designed to automate and aid in the daily tasks of GINDUMAC intern.

# Usage

1. Install Python3 along with pip on your computer, you can follow the online method you prefer(or even ask ChatGPT/Gemini).

2. Install depenencies specified in the ´requirements.txt´ file: `pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt`.

3. Run the main file, `final_gui_wlcpage.py`. `python3 final_gui_wlcpage.py`.

# Recommended install

It's highly recommended to install the project dependencies within a Python virtual environment (venv). A virtual environment creates an isolated space for your project's dependencies, preventing conflicts with other Python projects or your system's global Python installation. This makes your project more portable, reproducible, and reduces the risk of breaking other applications that rely on different package versions.
To set up and activate a virtual environment:
 * Create the virtual environment:
   `python3 -m venv venv`

   This command creates a directory named venv (you can choose a different name if you prefer) in your project root, containing the virtual environment files.
 * Activate the virtual environment:
   * On macOS and Linux:
     `source venv/bin/activate`

   * On Windows (Command Prompt):
     `venv\Scripts\activate.bat`

   * On Windows (PowerShell):
     `.\venv\Scripts\Activate.ps1`

   Once activated, your terminal prompt will typically show (venv) at the beginning, indicating that you're operating within the virtual environment.
 * Install dependencies specified in the requirements.txt file:
   `pip install -r requirements.txt`

   or
   `python3 -m pip install -r requirements.txt`

   Note: When your virtual environment is active, pip and python3 commands will automatically refer to the packages and interpreter within the virtual environment.
 * Run the main file, final_gui_wlcpage.py:
   `python3 final_gui_wlcpage.py`

When you're finished working on your project, you can deactivate the virtual environment by simply typing deactivate in your terminal.

# MAIN files

Please note there are 2 different main files, 1 is dedicated to macOS due to split view issues(`main_gui_mac.py`) while the other one is quite generic(works on ubuntu yet don't know if it will work on windows too).

# Module and Template Cheatsheet
This document provides a quick reference for the template files and placeholders used by each main module in your application.

1. Leads Template Tab
Module File: modules/leads.py

Functionality: This is the most advanced tab. It dynamically parses pasted text to generate a reply.

Templates File: templates.json

These templates are managed through the UI by clicking the "Manage Templates" button.

Parsing Rules File: parsing_rules.json

This file controls how information is extracted from the text. You can edit these rules by clicking the "Manage Parsing Rules" button.

Placeholders:

{client_name}

{machine_name}

{location}

{link}

2. Leads Follow-up Tab
Module File: modules/email_sent.py

Functionality: Provides simple, static follow-up messages.

Templates File: None. The templates are hardcoded directly inside the modules/email_sent.py file and cannot be changed from the UI.

Placeholders: None.

3. Contacts Tab
Module File: modules/contacts.py

Functionality: Generates follow-up emails for sellers from a CSV file.

Templates File: seller_templates.json

This is a simple JSON file. To edit these templates, you must manually open and edit the file in a text editor.

Placeholders:

{name}

4. Metabase Tab
Module File: modules/metabase.py

Functionality: Generates initial contact emails for leads from a CSV file.

Templates File: lead_templates.json

Similar to the Contacts tab, you must manually open and edit this file to change the templates.

Placeholders:

{name}

{machine}

{price}

{link}
